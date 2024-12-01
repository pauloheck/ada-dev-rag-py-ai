"""
Módulo core com funções de inicialização
"""
from .rag import RAG

def init_rag(persist_directory: str = "chroma_db") -> RAG:
    """
    Inicializa o sistema RAG
    
    Args:
        persist_directory: Diretório para persistir a base vetorial
        
    Returns:
        Instância do sistema RAG
    """
    return RAG(persist_directory=persist_directory)

def init_llm():
    """
    Inicializa o modelo LLM
    
    Returns:
        Instância do modelo LLM
    """
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0
    )

def create_qa_chain(llm, rag):
    """
    Cria uma chain de pergunta e resposta
    
    Args:
        llm: Modelo de linguagem
        rag: Sistema RAG
        
    Returns:
        Chain de QA
    """
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain_core.prompts import ChatPromptTemplate
    from langchain.chains import create_retrieval_chain
    from langchain_core.output_parsers import StrOutputParser
    
    # Template do prompt
    prompt = ChatPromptTemplate.from_template("""Responda a pergunta usando apenas o contexto fornecido. Se você não conseguir responder a pergunta com o contexto, diga que não tem informação suficiente.

    Contexto: {context}
    
    Pergunta: {input}
    """)
    
    # Cria a chain para processar documentos
    document_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=prompt,
        document_variable_name="context",
        output_parser=StrOutputParser()
    )
    
    # Cria a chain de recuperação
    retrieval_chain = create_retrieval_chain(
        rag.vectordb.as_retriever(),
        document_chain
    )
    
    return retrieval_chain
