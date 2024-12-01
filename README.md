# Configuração do Ambiente Virtual Python

Este guia explica como configurar e usar o ambiente virtual (venv) para este projeto.

## Pré-requisitos

- Python 3.12 instalado
- Acesso ao PowerShell ou Command Prompt (Windows)

## Configuração do Ambiente Virtual

### 1. Criar o Ambiente Virtual

```powershell
# Usando Python 3.12 específicamente
py -3.12 -m venv .venv
```

### 2. Ativar o Ambiente Virtual

#### No Windows:

PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

Command Prompt:
```cmd
.\.venv\Scripts\activate.bat
```

#### No Linux/MacOS:
```bash
source .venv/bin/activate
```

Para confirmar que o ambiente virtual está ativo, você verá `(.venv)` no início do prompt.

### 3. Desativar o Ambiente Virtual

Quando quiser sair do ambiente virtual:
```bash
deactivate
```

## Gerenciamento de Pacotes

### Instalar Dependências
```powershell
# Instalar um pacote específico
pip install nome-do-pacote

# Instalar todos os pacotes do requirements.txt
pip install -r requirements.txt
```

### Gerar requirements.txt
```powershell
pip freeze > requirements.txt
```

## Variáveis de Ambiente

Este projeto usa `python-dotenv` para gerenciar variáveis de ambiente.

1. Copie o arquivo `.env.example` para um novo arquivo chamado `.env`:
```powershell
copy .env.example .env
```

2. Edite o arquivo `.env` com suas configurações reais

3. No código Python, use as variáveis assim:
```python
from dotenv import load_dotenv
import os

# Carrega as variáveis do arquivo .env
load_dotenv()

# Acessa as variáveis
api_key = os.getenv('API_KEY')
```

## Running the FastAPI Application

To start the FastAPI application using Uvicorn, use the following command:

```bash
uvicorn src.ada_dev_rag_py_ai.api:app --host 0.0.0.0 --port 8000
```

### Explanation

- **`uvicorn`**: The command to run the Uvicorn server.
- **`src.ada_dev_rag_py_ai.api:app`**: Specifies the application to run, where `src.ada_dev_rag_py_ai.api` is the module path and `app` is the ASGI application instance.
- **`--host 0.0.0.0`**: Makes the application accessible from any network interface on the machine.
- **`--port 8000`**: The port on which the application will listen for incoming HTTP requests.

This command is typically used during development to run the FastAPI application locally. For production deployments, consider using a more robust setup with a process manager and a reverse proxy.

## Boas Práticas

1. **SEMPRE** use o ambiente virtual ao trabalhar no projeto
2. **NUNCA** comite o arquivo `.env` no git
3. Mantenha o `requirements.txt` atualizado
4. Atualize o `.env.example` quando adicionar novas variáveis de ambiente

## Solução de Problemas

### Erro ao Ativar o Ambiente Virtual no PowerShell
Se encontrar erro de permissão no PowerShell, execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Verificar Versão do Python no Ambiente Virtual
```powershell
python --version
```

### Listar Pacotes Instalados
```powershell
pip list
```
