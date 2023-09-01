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
    html.Div([
        dcc.Dropdown(
            id='delete-dropdown',
            options=[],
            value=None,  # Valor inicial é None
            placeholder='Selecione um arquivo para deletar'
        ),
        html.Button('Deletar Arquivo', id='delete-button'),
    ]),
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

@app.callback(Output('delete-dropdown', 'options'),
              Input('output-data', 'children'),
              State('delete-dropdown', 'value'),
              prevent_initial_call=True)
def atualizar_lista_arquivos(_, selected_file):
    bucket_name = 'seu-nome-de-bucket'
    files = listar_arquivos_bucket(bucket_name)
    
    dropdown_options = [{'label': file, 'value': file} for file in files]
    
    return dropdown_options

@app.callback(Output('delete-dropdown', 'value'),  # Define o valor da lista suspensa
              Output('file-list', 'children'),
              Input('output-data', 'children'),
              Input('delete-button', 'n_clicks'),
              State('delete-dropdown', 'value'),
              State('file-list', 'children'),
              prevent_initial_call=True)
def atualizar_lista_arquivos(_, delete_clicks, selected_file, file_links_state):
    bucket_name = 'seu-nome-de-bucket'
    files = listar_arquivos_bucket(bucket_name)
    
    updated_file_links = []
    
    if delete_clicks and selected_file:
        if selected_file in files:
            excluir_arquivo_bucket(bucket_name, selected_file)
            selected_file = None  # Define o valor da lista suspensa como None após a exclusão
    
    for file in files:
        file_link = dcc.Link(file, href=f'/download/{file}', target='_blank')
        updated_file_links.append(html.Div([
            file_link,
            html.Br(),
        ]))
    
    return selected_file, updated_file_links  # Retorna o valor para a lista suspensa

@server.route('/download/<path:filename>')
def download_file(filename):
    bucket_name = 'seu-nome-de-bucket'
    file_stream = s3_client.get_object(Bucket=bucket_name, Key=filename)['Body'].read()
    
    response = flask.Response(file_stream)
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

if __name__ == '__main__':
    app.run_server(debug=True)
