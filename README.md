## Guia de Execução de Projeto


#### Para utilizar o vDB via docker:

##### Para verificar detalhes sobre o vDB na forma de dashboard:

http://localhost:6333/dashboard

#### Para execução do front-end:

`streamlit run app.py`

#### Para executar o rag_service:

`python3.11 rag_service.py docs`

<span style="color:red; font-style: italic;">Obs: Deve-se indicar o caminho dos documentos, neste caso, o caminho é `docs`. Sempre que executado, o service processa todos os documentos dentro da pasta indicada.</span>