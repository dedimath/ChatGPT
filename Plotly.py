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
    html.Div(id='s3-tree')
])

@app.callback(
    Output('s3-tree', 'children'),
    Output('s3-tree', 'style'),
    Input('s3-tree', 'n_clicks'),
    prevent_initial_call=True
)
def create_s3_tree(n_clicks):
    objetos = listar_objetos_s3('')
    tree_structure = '<div id="jstree">'
    
    for obj in objetos:
        if '/' in obj:
            subdir = obj.split('/')[0]
            tree_structure += f'<li data-jstree=\'{{ "icon" : "fa fa-folder" }}\'>{subdir}</li>'
    
    tree_structure += '</div>'
    
    script = f"""
    <script>
        $('#jstree').jstree({{
            "core" : {{
                "data" : [
                    {tree_structure}
                ]
            }}
        }});
    </script>
    """
    
    return [dcc.Markdown(script)], {'overflow-y': 'scroll', 'height': '400px'}

def listar_objetos_s3(prefix):
    objetos = []
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    for obj in response.get('Contents', []):
        objetos.append(obj['Key'])
    return objetos

if __name__ == '__main__':
    app.run_server(debug=True)