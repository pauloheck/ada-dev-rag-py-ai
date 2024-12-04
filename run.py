"""
Script de entrada para executar o sistema RAG
"""
from src.ada_dev_rag_py_ai.api import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
