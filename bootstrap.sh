#!/usr/bin/env bash
# bootstrap-cloudwatch-logs.sh
# Configura o Amazon CloudWatch Agent no EMR para enviar logs de bootstrap, steps e scripts customizados.
# Uso opcional de variáveis de ambiente/args:
#   LOG_GROUP_PREFIX (default: /emr)
#   RETENTION_DAYS   (default: 14)
#   REGION           (detectado via IMDS se não informado)

set -euo pipefail

LOG_GROUP_PREFIX="${LOG_GROUP_PREFIX:-/emr}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
REGION="${REGION:-}"

# --- Descobrir região via IMDSv2, se necessário ---
if [[ -z "${REGION}" ]]; then
  TOKEN="$(curl -sS -X PUT 'http://169.254.169.254/latest/api/token' -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' || true)"
  REGION="$(curl -sS -H "X-aws-ec2-metadata-token: ${TOKEN}" http://169.254.169.254/latest/dynamic/instance-identity/document \
           | python -c 'import sys,json; print(json.load(sys.stdin)["region"])' 2>/dev/null || true)"
fi
if [[ -z "${REGION}" ]]; then
  echo "Não foi possível detectar a região; defina REGION no bootstrap." >&2
  exit 1
fi

# --- Identificadores do cluster e do nó ---
CLUSTER_ID="$(python - <<'PY'
import json
print(json.load(open('/mnt/var/lib/info/job-flow.json'))['jobFlowId'])
PY
)"
NODE_ROLE="core-or-task"
if grep -q '"isMaster": *true' /mnt/var/lib/info/instance.json 2>/dev/null; then
  NODE_ROLE="primary"
fi

# --- Garantir CloudWatch Agent instalado ---
if [[ ! -x /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl ]]; then
  echo "Instalando Amazon CloudWatch Agent..."
  curl -fsSL -o /tmp/amazon-cloudwatch-agent.rpm \
    https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
  rpm -Uvh --force /tmp/amazon-cloudwatch-agent.rpm
fi

# --- Diretório para logs de scripts customizados + wrapper ---
CUSTOM_DIR="/mnt/var/log/custom-scripts"
mkdir -p "${CUSTOM_DIR}"
chmod 775 "${CUSTOM_DIR}"

cat >/usr/local/bin/run-with-logs <<'WRAP'
#!/usr/bin/env bash
# Uso: run-with-logs <nome> -- <comando e args...>
set -euo pipefail
if [[ $# -lt 2 ]]; then
  echo "Uso: $0 <nome> -- <comando...>" >&2; exit 2
fi
NAME="$1"; shift
if [[ "${1:-}" == "--" ]]; then shift; fi
LOGDIR="/mnt/var/log/custom-scripts"
LOGFILE="${LOGDIR}/${NAME}.log"
mkdir -p "$LOGDIR"; touch "$LOGFILE"; chmod 664 "$LOGFILE"
{
  echo "===== $(date -Is) START: ${NAME} on $(hostname) ====="
  "$@"
  RC=$?
  echo "===== $(date -Is) END: ${NAME} (rc=${RC}) ====="
  exit $RC
} 2>&1 | tee -a "$LOGFILE"
WRAP
chmod +x /usr/local/bin/run-with-logs

# --- Gerar configuração do CloudWatch Agent ---
CFG_DIR="/opt/aws/amazon-cloudwatch-agent/etc"
CFG_FILE="${CFG_DIR}/amazon-cloudwatch-agent.json"
mkdir -p "${CFG_DIR}"

cat >"${CFG_FILE}" <<CFG
{
  "agent": {
    "region": "${REGION}",
    "metrics_collection_interval": 60,
    "debug": false,
    "logfile": "/opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log"
  },
  "logs": {
    "force_flush_interval": 5,
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/mnt/var/log/bootstrap-actions/*/stdout",
            "log_group_name": "${LOG_GROUP_PREFIX}/${CLUSTER_ID}/bootstrap",
            "log_stream_name": "${NODE_ROLE}/{instance_id}/stdout",
            "retention_in_days": ${RETENTION_DAYS}
          },
          {
            "file_path": "/mnt/var/log/bootstrap-actions/*/stderr",
            "log_group_name": "${LOG_GROUP_PREFIX}/${CLUSTER_ID}/bootstrap",
            "log_stream_name": "${NODE_ROLE}/{instance_id}/stderr",
            "retention_in_days": ${RETENTION_DAYS}
          },
          {
            "file_path": "/emr/instance-controller/log/bootstrap-actions",
            "log_group_name": "${LOG_GROUP_PREFIX}/${CLUSTER_ID}/bootstrap",
            "log_stream_name": "${NODE_ROLE}/{instance_id}/controller",
            "retention_in_days": ${RETENTION_DAYS}
          },
          {
            "file_path": "/mnt/var/log/hadoop/steps/*/controller",
            "log_group_name": "${LOG_GROUP_PREFIX}/${CLUSTER_ID}/steps",
            "log_stream_name": "${NODE_ROLE}/{instance_id}/controller",
            "retention_in_days": ${RETENTION_DAYS}
          },
          {
            "file_path": "/mnt/var/log/hadoop/steps/*/stdout",
            "log_group_name": "${LOG_GROUP_PREFIX}/${CLUSTER_ID}/steps",
            "log_stream_name": "${NODE_ROLE}/{instance_id}/stdout",
            "retention_in_days": ${RETENTION_DAYS}
          },
          {
            "file_path": "/mnt/var/log/hadoop/steps/*/stderr",
            "log_group_name": "${LOG_GROUP_PREFIX}/${CLUSTER_ID}/steps",
            "log_stream_name": "${NODE_ROLE}/{instance_id}/stderr",
            "retention_in_days": ${RETENTION_DAYS}
          },
          {
            "file_path": "/mnt/var/log/custom-scripts/*.log",
            "log_group_name": "${LOG_GROUP_PREFIX}/${CLUSTER_ID}/scripts",
            "log_stream_name": "${NODE_ROLE}/{instance_id}/custom",
            "retention_in_days": ${RETENTION_DAYS}
          }
        ]
      }
    }
  }
}
CFG

# --- Iniciar (ou reiniciar) o agente ---
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a stop || true
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -m ec2 -a fetch-config -c "file:${CFG_FILE}" -s

systemctl enable amazon-cloudwatch-agent || true
echo "CloudWatch Agent configurado. Enviando logs para ${LOG_GROUP_PREFIX}/${CLUSTER_ID}/..."