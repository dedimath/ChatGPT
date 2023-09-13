import os
import dash
import flask
from dash import dcc, html
from dash.dependencies import Input, Output, State
import boto3

app = dash.Dash(__name__)
server = app.server  # Obtém o servidor do Dash para configuração do Flask

s3_client = boto3.client('s3')

# Configurações da paginação
itens_por_pagina = 5  # Defina o número de itens por página

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
            placeholder='Selecione um arquivo para deletar',
        ),
        html.Button('Voltar', id='prev-button', n_clicks=0),  # Botão de voltar
        html.Button('Avançar', id='next-button', n_clicks=0),  # Botão de avançar
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
              Input('prev-button', 'n_clicks'),
              Input('next-button', 'n_clicks'),
              State('delete-dropdown', 'value'),
              State('delete-dropdown', 'options'),
              prevent_initial_call=True)
def atualizar_lista_arquivos(_, prev_clicks, next_clicks, selected_file, current_options):
    bucket_name = 'seu-nome-de-bucket'
    files = listar_arquivos_bucket(bucket_name)

    # Verifica quantas páginas são necessárias
    num_paginas = len(files) // itens_por_pagina
    if len(files) % itens_por_pagina != 0:
        num_paginas += 1

    # Obtenha o índice da página atual com base no valor atual da lista suspensa
    pagina_atual = 0
    if selected_file:
        pagina_atual = current_options.index({'label': selected_file, 'value': selected_file}) // itens_por_pagina

    # Verifica qual botão foi clicado
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'prev-button'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Calcula a nova página com base no botão clicado
    if button_id == 'prev-button' and pagina_atual > 0:
        pagina_atual -= 1
    elif button_id == 'next-button' and pagina_atual < num_paginas - 1:
        pagina_atual += 1

    # Calcula os índices de início e fim para a página atual
    inicio = pagina_atual * itens_por_pagina
    fim = inicio + itens_por_pagina

    # Cria as opções da lista suspensa para a página atual
    dropdown_options = [{'label': file, 'value': file} for file in files[inicio:fim]]

    return dropdown_options

@app.callback(Output('file-list', 'children'),
              Input('output-data', 'children'),
              Input('prev-button', 'n_clicks'),
              Input('next-button', 'n_clicks'),
              State('delete-dropdown', 'value'),
              State('file-list', 'children'),
              prevent_initial_call=True)
def atualizar_lista_arquivos(_, prev_clicks, next_clicks, selected_file, file_links_state):
    bucket_name = 'seu-nome-de-bucket'
    files = listar_arquivos_bucket(bucket_name)
    
    updated_file_links = []
    
    if prev_clicks or next_clicks:
        return updated_file_links  # Não faça nada se o botão de paginação for clicado
    
    for file in files:
        file_link = dcc.Link(file, href=f'/download/{file}', target='_blank')
        updated_file_links.append(html.Div([
            file_link,
            html.Br(),
        ]))
    
    return updated_file_links

@server.route('/download/<path:filename>')
def download_file(filename):
    bucket_name = 'seu-nome-de-bucket'
    file_stream = s3_client.get_object(Bucket=bucket_name, Key=filename)['Body'].read()
    
    response = flask.Response(file_stream)
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

if __name__ == '__main__':
    app.run_server(debug=True)