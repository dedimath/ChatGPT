import os
import dash
import flask
from dash import dcc, html
from dash.dependencies import Input, Output, State
import boto3

app = dash.Dash(__name__)
server = app.server  # Obtém o servidor do Dash para configuração do Flask

s3_client = boto3.client('s3')

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Arraste e solte ou ',
            html.A('selecione um arquivo')
        ]),
        multiple=False
    ),
    html.Div(id='output-data'),
    html.Div(id='file-list'),
])

def enviar_para_s3(nome_arquivo, conteudo_arquivo):
    bucket_name = 'seu-nome-de-bucket'
    s3_client.upload_fileobj(conteudo_arquivo, bucket_name, nome_arquivo)

def listar_arquivos_bucket(bucket_name):
    files = []
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in response:
        files = [obj['Key'] for obj in response['Contents']]
    return files

def excluir_arquivo_bucket(bucket_name, filename):
    s3_client.delete_object(Bucket=bucket_name, Key=filename)

@app.callback(Output('output-data', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              prevent_initial_call=True)
def processar_upload(contents, filename):
    if contents is None:
        return html.Div()

    # Converter o conteúdo do arquivo para bytes
    conteudo_arquivo = contents.encode('utf-8')

    # Enviar o arquivo para o S3
    enviar_para_s3(filename, conteudo_arquivo)

    return html.Div(f'Arquivo "{filename}" enviado para o S3.')

@app.callback(Output('file-list', 'children'),
              Input('output-data', 'children'),
              Input('file-list', 'children'),
              prevent_initial_call=True)
def exibir_lista_arquivos(_, file_links):
    bucket_name = 'seu-nome-de-bucket'
    files = listar_arquivos_bucket(bucket_name)
    
    file_links = []
    for file in files:
        file_link = dcc.Link(file, href=f'/download/{file}', target='_blank')
        delete_button = html.Button(f'Deletar {file}', id={'type': 'delete-button', 'index': file})
        
        file_links.append(html.Div([
            file_link,
            delete_button,
            html.Br(),
        ]))
    
    return html.Div([
        html.Hr(),
        html.H3('Lista de Arquivos no Bucket S3:'),
        *file_links
    ])

@app.callback(
    Output('hidden-div', 'children'),
    Input({'type': 'delete-button', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def deletar_arquivo(n_clicks_list):
    bucket_name = 'seu-nome-de-bucket'
    files = listar_arquivos_bucket(bucket_name)
    
    updated_file_links = []
    ctx = dash.callback_context
    
    if ctx.triggered:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        idx = triggered_id['index']
        if idx in files:
            excluir_arquivo_bucket(bucket_name, idx)
    
    return None

@app.callback(
    Output('file-list', 'children'),
    Input('hidden-div', 'children'),
    State('file-list', 'children'),
    prevent_initial_call=True
)
def atualizar_lista_arquivos(_, file_links):
    return exibir_lista_arquivos(_, file_links)

@server.route('/download/<path:filename>')
def download_file(filename):
    bucket_name = 'seu-nome-de-bucket'
    file_stream = s3_client.get_object(Bucket=bucket_name, Key=filename)['Body'].read()
    
    response = flask.Response(file_stream)
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

if __name__ == '__main__':
    app.run_server(debug=True)
