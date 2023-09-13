import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import boto3

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Configurar o cliente S3
s3_client = boto3.client('s3')

# Nome do bucket S3
bucket_name = 'seu-bucket-s3'

def listar_objetos_s3(prefix):
    objetos = []
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    for obj in response.get('Contents', []):
        objetos.append(obj['Key'])
    return objetos

def construir_arvore_s3(prefix):
    objetos = listar_objetos_s3(prefix)
    elementos = []
    for obj in objetos:
        if '/' in obj[len(prefix):]:
            subdir = obj[len(prefix):].split('/')[0]
            elementos.append(html.Button(f"{subdir}/", id={'type': 'dir-button', 'index': subdir}))
        else:
            elementos.append(html.Div(obj[len(prefix):]))
    return elementos

app.layout = dbc.Container([
    html.H1('Árvore de Diretórios do Amazon S3'),
    html.Div(id='tree'),
])

@app.callback(
    Output('tree', 'children'),
    Input({'type': 'dir-button', 'index': Input('tree', 'children')}, 'n_clicks'),
    prevent_initial_call=True
)
def toggle_dir_contents(n_clicks, children):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    subdir = changed_id.split('.')[1]
    prefix = f"{subdir}/"
    return construir_arvore_s3(prefix)

if __name__ == '__main__':
    app.run_server(debug=True)