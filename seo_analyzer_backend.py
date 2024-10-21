from flask import Flask, request, jsonify, render_template
from dash import Dash, html, dcc, Input, Output, State  # Importar Input, Output e State corretamente
import requests
from bs4 import BeautifulSoup

# Inicializar o Flask
server = Flask(__name__)

# Definir a rota principal para o template HTML
@server.route('/')
def index():
    return render_template('layout.html')

# Inicializar o Dash e apontar para o servidor Flask
app_dash = Dash(__name__, server=server, url_base_pathname='/dashboard/')

# Layout do Dash com Bootstrap
app_dash.layout = html.Div([
    html.Link(href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css', rel='stylesheet'),  # CDN do Bootstrap
    html.Div(className="container mt-5", children=[
        html.H1('SEO Analyzer'),
        html.P('Use o Dashboard abaixo'),
        html.Div(className="d-flex align-items-center gap-2", children=[
            dcc.Input(id='url-input', type='text', placeholder='Enter URL', className="form-control mb-2"),
            html.Button('Analyze', id='analyze-button', n_clicks=0, className="btn btn-primary mb-2"),
        ]),
        html.Div(id='output-seo-data', className="mt-4")
    ]),
    html.Script(src="https://code.jquery.com/jquery-3.5.1.slim.min.js"),  # Scripts do Bootstrap (opcional)
    html.Script(src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.2/dist/umd/popper.min.js"),
    html.Script(src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js")
])

# Callback para processar o input e gerar a saída
@app_dash.callback(
    Output('output-seo-data', 'children'),
    Input('analyze-button', 'n_clicks'),
    State('url-input', 'value')
)
def update_output(n_clicks, value):
    if n_clicks > 0 and value:
        try:
            response = requests.post('http://127.0.0.1:5000/analyze', json={'url': value})
            response.raise_for_status()  # Verifica se a resposta foi bem-sucedida
            seo_data = response.json()
            return html.Div([
                html.H3(f"Title: {seo_data['title']}", className="h5"),
                html.P(f"Meta Description: {seo_data['meta_description']}", className="text-muted"),
                html.H4("Headers:", className="h6"),
                html.Ul([html.Li(header) for header in seo_data['headers']])
            ])
        except requests.exceptions.RequestException as e:
            return html.Div([html.P(f"Error: {str(e)}", className="text-danger")])
    return html.Div()

# Endpoint para analisar a URL
@server.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        url = data.get('url')

        # Fazer a requisição para a URL
        response = requests.get(url)
        response.raise_for_status()  # Levanta um erro se a requisição falhar

        # Analisar o conteúdo da página
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extrair informações relevantes
        title = soup.title.string if soup.title else 'Título não encontrado'
        meta_description = ''
        for meta in soup.find_all('meta'):
            if 'name' in meta.attrs and meta['name'].lower() == 'description':
                meta_description = meta['content']
                break
        
        headers = []
        for i in range(1, 7):  # Para h1 a h6
            headers.extend([header.get_text() for header in soup.find_all(f'h{i}')])

        return jsonify({
            'title': title,
            'meta_description': meta_description if meta_description else 'Meta descrição não encontrada',
            'headers': headers if headers else ['Nenhum cabeçalho encontrado']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Retorna um erro 500 com a mensagem do erro

# Executa o servidor Flask e o aplicativo Dash
if __name__ == '__main__':
    server.run(debug=True)
