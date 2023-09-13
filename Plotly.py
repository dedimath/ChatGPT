import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
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
    tree = html.Div()
    for obj in objetos:
        if '/' in obj[len(prefix):]:
            subdir = obj[len(prefix):].split('/')[0]
            if not any(subdir in div['props']['children'] for div in tree.children):
                tree.children.append(html.Div([
                    html.Button(f"{subdir}/", id={'type': 'dir-button', 'index': subdir}),
                    html.Div(id={'type': 'dir-content', 'index': subdir}, style={'display': 'none'})
                ]))
        else:
            tree.children.append(html.Div(obj[len(prefix):]))
    return tree

app.layout = dbc.Container([
    html.H1('Árvore de Diretórios do Amazon S3'),
    construir_arvore_s3(''),
])

@app.callback(
    Output({'type': 'dir-content', 'index': Input('dir-button', 'n_clicks')}, 'style'),
    Input({'type': 'dir-button', 'index': 'ALL'}, 'n_clicks'),
    prevent_initial_call=True
)
def toggle_dir_contents(n_clicks):
    if n_clicks % 2 == 0:
        return {'display': 'none'}
    else:
        return {'display': 'block'}

if __name__ == '__main__':
    app.run_server(debug=True)