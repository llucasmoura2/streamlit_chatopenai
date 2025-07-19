import os
from decouple import config
import streamlit as st
from dotenv import load_dotenv
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain.prompts import PromptTemplate
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_openai import ChatOpenAI


load_dotenv()

api_key=os.getenv('teste_api')


st.set_page_config(
    page_title='Estoque GPT',
    page_icon='📦',
)

st.markdown("## 📂 Selecione ou Envie um Banco de Dados (.db)")

local_dbs = [f for f in os.listdir() if f.endswith(".db")]


db_mode = st.radio("Como deseja utilizar o banco de dados?", ["Selecionar existente", "Enviar novo arquivo"])

db = None

# Seleção de banco existente
if db_mode == "Selecionar existente":
    if local_dbs:
        selected_db = st.selectbox("Escolha um banco de dados:", local_dbs)
        if selected_db:
            db_path = f"sqlite:///{selected_db}"
            db = SQLDatabase.from_uri(db_path)
            st.success(f"Banco de dados `{selected_db}` carregado com sucesso.")
    else:
        st.warning("Nenhum arquivo .db foi encontrado na pasta.")

# Upload de novo banco
else:
    uploaded_file = st.file_uploader("Envie um arquivo .db", type="db")
    if uploaded_file is not None:
        os.makedirs("temp_uploads", exist_ok=True)
        saved_path = os.path.join("temp_uploads", uploaded_file.name)
        with open(saved_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        db_path = f"sqlite:///{saved_path}"
        db = SQLDatabase.from_uri(db_path)
        st.success(f"Arquivo `{uploaded_file.name}` carregado com sucesso.")


if db is not None:
    st.info("✅ Banco de dados pronto para uso com o agente.")
else:
    st.stop()

# Esse é o st.header
st.markdown("<h1 style='text-align: center;'>Assistente de Estoque</h1>", unsafe_allow_html=True)

model_options = [
    'gpt-4',
    'gpt-4-turbo',
    'gpt-4o-mini',
    'gpt-4o',
]

selected_model = st.sidebar.selectbox(
    label='Selecione o modelo LLM.',
    options=model_options,
)

st.sidebar.markdown('### Sobre')
st.sidebar.markdown("Somos uma Empresa de tecnologia focada em IA.")

st.markdown("<h3 style='text-align: center;'> Faça pergunta sobre o estoque de produtos, preços e reposições.</h3>", unsafe_allow_html=True)
user_question = st.text_input('O que você deseja saber sobre o estoque?')


model = ChatOpenAI(
    model= selected_model,
    openai_api_key=api_key,
)


toolkit = SQLDatabaseToolkit(
    db=db,
    llm=model,
    top_k=5,
)

system_message = hub.pull('hwchase17/react')

agent = create_react_agent(
    llm=model,
    tools=toolkit.get_tools(),
    prompt=system_message,
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=toolkit.get_tools(),
    verbose=True,
    handle_parsing_errors=True,
)

prompt = '''
Use as ferramentas necessárias para responder perguntas relacionadas ao
estoque de produtos. Você fornecerá insights sobre produtos, preços, 
reposição de estoque e relatórios conforme solicitado pelo usuário.
A resposta final deve ter uma formatação amigável de visualização para o usuário.
Sempre responda em português brasileiro.
Pergunta: {q}
'''

prompt_template = PromptTemplate.from_template(prompt)


if st.button('Consultar'):
    if user_question:
        with st.spinner('Consultando o banco de dados:'):
            formatted_prompt = prompt_template.format(q=user_question)
            output = agent_executor.invoke(
                {'input': formatted_prompt}
            )
            st.markdown(output.get('output'))
    else:
        st.warning('Por favor, faça uma pergunta')
