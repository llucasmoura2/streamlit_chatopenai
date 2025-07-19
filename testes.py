from dotenv import load_dotenv
import os

load_dotenv()  # carrega as variáveis do arquivo .env para o os.environ

print("Valor de teste_api em os.environ:", os.environ.get("teste_api"))