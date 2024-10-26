import os
from dotenv import load_dotenv
from fastapi import FastAPI
from qdrant_client import QdrantClient
from langchain_qdrant import Qdrant
from pydantic import BaseModel
from langchain.embeddings import HuggingFaceEmbeddings

# Carregando variáveis de ambiente
load_dotenv()
nvidia_key = os.getenv("NVIDIA_KEY")

# Definindo uma classe Item que herda de BaseModel
class Item(BaseModel):
    query: str

# Definindo o modelo tokenizador
model_name_ = os.getenv("MODEL_NAME")
# Configurações do modelo
model_cfgs = {'device': 'cpu'}
# Configurações de codificação para que todos sejam formatados na mesma escala
ecode_cfgs = {'normalize_embeddings': True}

# Inicializando a classe de embeddings
hf = HuggingFaceEmbeddings(model_name=model_name_,
                           model_kwargs=model_cfgs,
                           encode_kwargs=ecode_cfgs)

user_nvidia_api = False

# Verificar se a chave Nvidia é disponível
if nvidia_key != "":
    from openai import OpenAI

    client_llm = OpenAI(base_url="https://integrate.api.nvidia.com/v1",
                        api_key=nvidia_key)
    user_nvidia_api = True
else:
    print("Não foi possível usar o LLM!")

# Criando a instância para conectar ao banco vetorial
client = QdrantClient("http://localhost:6333")

# Definindo o nome da coleção
collection_name = "vdb-study"

qdrant = Qdrant(client, collection_name, hf)

# ----------------- API com FastAPI ----------------- #
# Criando a instância de FastAPI
app = FastAPI()

# Definindo a rota raiz com o método GET
@app.get("/")
async def root():
    return {"message": "RAG project!"}

@app.post("/llm_calls")
async def llm_calls(item: Item):
    try:
        # Recebendo a query do usuário
        query = item.query

        # Realizando busca por similaridade usando QdrantClient
        search_result = qdrant.similarity_search(query=query, k=10)

        # Inicializando a lista de resultados
        list_res = []
        context = ""
        mappings = {}

        # Construção de contexto com base em resultados
        for i, res in enumerate(search_result):
            context += f"{i}\n{res.page_content}\n\n"
            mappings[i] = res.metadata.get("path")
            list_res.append({"id": i, "path": res.metadata.get("path"), "content": res.page_content})

        # Definindo as mensagens para o LLM
        rolemsg = {"role": "system",
                   "content": "Responda à pergunta do usuário usando documentos fornecidos no contexto. No contexto estão documentos que devem conter uma resposta. Sempre faça referência ao ID do documento (entre colchetes, por exemplo [0],[1]) do documento que foi usado para fazer uma consulta. Use quantas citações e documentos forem necessários para responder à pergunta."}

        messages = [rolemsg, {"role": "user", "content": f"Documents:\n{context}\n\nQuestion: {query}"}]

        # Uso de API Nvidia
        if user_nvidia_api:
            answer = client_llm.chat.completions.create(model=os.getenv("LLM_MODEL"),
                                                        messages=messages,
                                                        temperature=0.5,
                                                        top_p=1,
                                                        max_tokens=1024,
                                                        stream=False)
            response = answer.choices[0].message.content
        else:
            response = "Não foi possível usar o LLM!"

        return {"context": list_res, "answer": response}

    except Exception as e:
        error_message = f"Erro interno na API: {str(e)}"
        return {"error": error_message}, 500  # Retorna um erro 500 Internal Server Error