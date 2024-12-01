"""
Testes para o módulo main
"""
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
from ada_dev_rag_py_ai.main import main

@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
@patch('ada_dev_rag_py_ai.core.OpenAI')
def test_main_successful_interaction(mock_openai, mock_input, mock_stdout):
    """
    Testa uma interação bem-sucedida com o programa principal
    """
    # Configura os mocks
    mock_instance = MagicMock()
    mock_instance.predict.return_value = "Esta é uma resposta de teste"
    mock_openai.return_value = mock_instance
    
    # Simula o usuário fazendo uma pergunta e depois saindo
    mock_input.side_effect = ["Qual é a pergunta de teste?", "sair"]
    
    # Executa o programa principal
    with patch.dict('os.environ', {"OPENAI_API_KEY": "test-key"}):
        main()
    
    # Verifica as saídas
    output = mock_stdout.getvalue()
    assert "Inicializando o modelo LLM" in output
    assert "Esta é uma resposta de teste" in output
    assert "Encerrando o programa" in output

@patch('sys.stdout', new_callable=StringIO)
@patch('ada_dev_rag_py_ai.core.OpenAI')
def test_main_without_api_key(mock_openai, mock_stdout):
    """
    Testa o comportamento quando não há API key configurada
    """
    # Remove a API key do ambiente
    with patch.dict('os.environ', {}, clear=True):
        main()
    
    # Verifica se a mensagem de erro apropriada foi exibida
    output = mock_stdout.getvalue()
    assert "OPENAI_API_KEY não encontrada" in output

@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
@patch('ada_dev_rag_py_ai.core.OpenAI')
def test_main_with_api_error(mock_openai, mock_input, mock_stdout):
    """
    Testa o comportamento quando ocorre um erro na API
    """
    # Configura o mock para lançar uma exceção
    mock_instance = MagicMock()
    mock_instance.predict.side_effect = Exception("Erro de API simulado")
    mock_openai.return_value = mock_instance
    
    # Simula uma entrada do usuário
    mock_input.return_value = "Pergunta teste"
    
    # Executa o programa principal
    with patch.dict('os.environ', {"OPENAI_API_KEY": "test-key"}):
        main()
    
    # Verifica se a mensagem de erro apropriada foi exibida
    output = mock_stdout.getvalue()
    assert "Erro inesperado" in output
    assert "Erro de API simulado" in output
