"""
Testes para o módulo core
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from ada_dev_rag_py_ai.core import init_llm

def test_init_llm_without_api_key():
    """
    Testa se a função init_llm levanta um erro quando não há API key configurada
    """
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="OPENAI_API_KEY não encontrada nas variáveis de ambiente"):
            init_llm()

def test_init_llm_with_api_key():
    """
    Testa se a função init_llm retorna uma instância do OpenAI quando há API key
    """
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        llm = init_llm()
        assert llm is not None

@patch('ada_dev_rag_py_ai.core.OpenAI')
def test_llm_prediction(mock_openai):
    """
    Testa se o LLM consegue fazer predições corretamente
    """
    # Configura o mock
    mock_instance = MagicMock()
    mock_instance.predict.return_value = "Python é uma linguagem de programação"
    mock_openai.return_value = mock_instance

    # Executa o teste
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        llm = init_llm()
        response = llm.predict("O que é Python?")
        assert response == "Python é uma linguagem de programação"
        mock_instance.predict.assert_called_once_with("O que é Python?")
