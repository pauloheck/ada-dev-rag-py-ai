"""
Testes para o módulo de chat
"""
import pytest
import asyncio
from datetime import datetime
from ada_dev_rag_py_ai.chat import RAGChat
from ada_dev_rag_py_ai.models import ChatMessage, ChatResponse

@pytest.fixture
def chat_instance():
    """Fixture que fornece uma instância do RAGChat"""
    return RAGChat()

@pytest.mark.asyncio
async def test_chat_basic_interaction(chat_instance):
    """Testa interação básica com o chat"""
    # Testa uma mensagem simples
    response = await chat_instance.chat("Olá, como você está?", include_context=False)
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_chat_with_context(chat_instance):
    """Testa chat com uso de contexto"""
    # Testa mensagem com contexto ativado
    response = await chat_instance.chat(
        "Qual a melhor forma de processar imagens no sistema?",
        include_context=True
    )
    assert isinstance(response, str)
    assert len(response) > 0

def test_chat_history_management(chat_instance):
    """Testa gerenciamento do histórico do chat"""
    # Verifica histórico inicial vazio
    initial_history = chat_instance.get_chat_history()
    assert isinstance(initial_history, list)
    assert len(initial_history) == 0
    
    # Adiciona algumas mensagens ao histórico
    asyncio.run(chat_instance.chat("Mensagem 1", include_context=False))
    asyncio.run(chat_instance.chat("Mensagem 2", include_context=False))
    
    # Verifica histórico atualizado
    updated_history = chat_instance.get_chat_history()
    assert len(updated_history) == 4  # 2 mensagens do usuário + 2 respostas
    
    # Verifica estrutura das mensagens
    for msg in updated_history:
        assert "role" in msg
        assert "content" in msg
        assert "timestamp" in msg
        assert isinstance(msg["timestamp"], str)
        
    # Testa limpeza do histórico
    chat_instance.clear_history()
    cleared_history = chat_instance.get_chat_history()
    assert len(cleared_history) == 0

@pytest.mark.asyncio
async def test_chat_error_handling(chat_instance):
    """Testa tratamento de erros do chat"""
    # Testa mensagem vazia
    with pytest.raises(Exception):
        await chat_instance.chat("", include_context=True)
    
    # Testa mensagem muito longa (100k caracteres)
    long_message = "x" * 100000
    with pytest.raises(Exception):
        await chat_instance.chat(long_message, include_context=True)

@pytest.mark.asyncio
async def test_chat_context_switching(chat_instance):
    """Testa alternância do uso de contexto"""
    # Testa com contexto
    response_with_context = await chat_instance.chat(
        "Como funciona o sistema RAG?",
        include_context=True
    )
    assert isinstance(response_with_context, str)
    
    # Testa sem contexto
    response_without_context = await chat_instance.chat(
        "Como funciona o sistema RAG?",
        include_context=False
    )
    assert isinstance(response_without_context, str)
    
    # As respostas devem ser diferentes
    assert response_with_context != response_without_context

def test_chat_timestamp_format(chat_instance):
    """Testa formato dos timestamps no histórico"""
    # Adiciona uma mensagem
    asyncio.run(chat_instance.chat("Teste de timestamp", include_context=False))
    
    # Verifica formato do timestamp
    history = chat_instance.get_chat_history()
    for msg in history:
        timestamp = msg["timestamp"]
        # Verifica se é possível fazer parse do timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            assert isinstance(dt, datetime)
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp}")

@pytest.mark.asyncio
async def test_chat_conversation_flow(chat_instance):
    """Testa fluxo de conversação"""
    # Simula uma conversa com múltiplas interações
    responses = []
    
    # Primeira interação
    responses.append(await chat_instance.chat(
        "Olá, gostaria de saber mais sobre o sistema",
        include_context=True
    ))
    
    # Segunda interação referenciando a primeira
    responses.append(await chat_instance.chat(
        "Pode me dar um exemplo prático?",
        include_context=True
    ))
    
    # Terceira interação com pergunta específica
    responses.append(await chat_instance.chat(
        "Como faço para processar imagens?",
        include_context=True
    ))
    
    # Verifica se todas as respostas são válidas
    for response in responses:
        assert isinstance(response, str)
        assert len(response) > 0
    
    # Verifica se o histórico manteve a ordem
    history = chat_instance.get_chat_history()
    assert len(history) == len(responses) * 2  # pergunta + resposta para cada interação
    
    # Verifica se os timestamps estão em ordem crescente
    timestamps = [datetime.fromisoformat(msg["timestamp"]) for msg in history]
    assert timestamps == sorted(timestamps)
