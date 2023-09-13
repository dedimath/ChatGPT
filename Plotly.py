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

app.layout = dbc.Container([
    html.H1('Árvore de Diretórios do Amazon S3'),
    html.Div(id='s3-tree'),
])

@app.callback(
    Output('s3-tree', 'children'),
    Input('s3-tree', 'n_clicks'),
    Input('s3-tree', 'data'),
    prevent_initial_call=True
)
def update_tree(n_clicks, data):
    if data is None:
        current_dir = ''
    else:
        current_dir = data['current_dir']

    objetos = listar_objetos_s3(current_dir)
    tree_elements = []

    for obj in objetos:
        if '/' in obj[len(current_dir):]:
            subdir = obj[len(current_dir):].split('/')[0]
            button = html.Button(f"{subdir}/", id={'type': 'dir-button', 'index': subdir, 'current_dir': current_dir})
            tree_elements.append(button)
        else:
            tree_elements.append(html.Div(obj[len(current_dir):]))

    return tree_elements

@app.callback(
    Output('s3-tree', 'data'),
    Input({'type': 'dir-button', 'index': Input('s3-tree', 'data')}, 'n_clicks'),
    prevent_initial_call=True
)
def handle_directory_click(n_clicks, data):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    subdir = changed_id.split('.')[1]
    current_dir = data['current_dir'] + subdir + '/'
    return {'current_dir': current_dir}

def listar_objetos_s3(prefix):
    objetos = []
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    for obj in response.get('Contents', []):
        objetos.append(obj['Key'])
    return objetos

if __name__ == '__main__':
    app.run_server(debug=True)