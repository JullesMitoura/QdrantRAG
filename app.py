import re
import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Definindo o título da página e configurações
st.set_page_config(page_title="RAG",
                   page_icon="💡",
                   layout="centered")
st.image("top.png", use_column_width=True)

# Contador para gerar chaves únicas para botões de download
download_button_counter = 0

def api_return(question_input):
    # Definindo o endereço da API que será utilizada para realizar consultas
    api_url = os.getenv("API_URL")

    # Criando o payload da requisição em formato json
    payload = json.dumps({"query": question_input})

    # Definindo o header da requisição
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    try:
        response = requests.request("POST", api_url, headers=headers, data=payload)
        response.raise_for_status()  # Lança uma exceção para códigos de status HTTP >= 400
        response_json = response.json()
        answer = json.loads(response.text)["answer"]
        documents = json.loads(response.text)['context']

        return answer, documents

    except requests.exceptions.RequestException as e:
        st.error(f"Erro na requisição: {e}")
        return "Erro na requisição", []
    except (json.JSONDecodeError, KeyError) as e:
        st.error(f"Erro ao decodificar resposta JSON: {e}")
        return "Resposta inválida do servidor", []

def chat():
    global download_button_counter  # Utilizando o contador global

    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm here to help you find informations."}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                with st.spinner("Thinking ... "):
                    answer, documents = api_return(prompt)
                    st.markdown(answer)

                    # Lista para armazenar IDs únicos de documentos já exibidos
                    displayed_document_ids = []

                    # Regex para encontrar todas as referências a documentos na resposta
                    ref_pattern = re.compile(r'\[[0-9]+\]')
                    referenced_documents = ref_pattern.findall(answer)

                    for ref in referenced_documents:
                        doc_id = int(ref.strip('[]'))
                        for doc in documents:
                            if doc['id'] == doc_id and doc['id'] not in displayed_document_ids:
                                displayed_document_ids.append(doc['id'])
                                with st.expander(f"{doc['id']} - {doc['path']}"):
                                    st.write(doc['content'])
                                    download_button_counter += 1  # Incrementando o contador
                                    st.download_button(f"Download document {download_button_counter}", doc['path'], file_name=os.path.basename(doc['path']))

            message = {"role": "assistant", "content": answer}
            st.session_state.messages.append(message)

# Chamando a função chat
chat()