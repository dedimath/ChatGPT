import boto3

def lambda_handler(event, context):
    # Nome da fila FIFO do SQS
    queue_name = 'sua-fila-fifo'

    # Inicializa o cliente do SQS
    sqs = boto3.client('sqs')

    # Obtém a URL da fila com base no nome
    response = sqs.get_queue_url(QueueName=queue_name)
    queue_url = response['QueueUrl']

    # Recebe mensagens da fila
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'All'
        ],
        MaxNumberOfMessages=1,  # Obtém uma única mensagem
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=0  # Não espere por mensagens, apenas verifique se há alguma
    )

    if 'Messages' in response:
        # Se há uma mensagem na fila, obtenha o corpo da mensagem
        message = response['Messages'][0]
        message_body = message['Body']
        
        # Exclua a mensagem da fila
        receipt_handle = message['ReceiptHandle']
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )

        return {
            "mensagem": message_body
        }
    else:
        # Se não há mensagens na fila, retorne 0
        return {
            "mensagem": "0"
        }