"""
Módulo para chat interativo usando RAG e OpenAI
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from .rag import RAG

class RAGChat:
    """
    Implementa chat interativo usando RAG e OpenAI
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo-1106"):
        """
        Inicializa o chat
        
        Args:
            model_name: Nome do modelo OpenAI a ser usado
        """
        self.rag = RAG()
        self.chat_model = ChatOpenAI(
            model_name=model_name,
            temperature=0.7
        )
        
        # Define o prompt base do sistema
        self.system_template = """Você é um assistente especializado que utiliza uma base de conhecimento para fornecer respostas precisas.
        
        Regras:
        1. Use o contexto fornecido para embasar suas respostas
        2. Se o contexto não for suficiente, indique claramente
        3. Mantenha um tom profissional mas amigável
        4. Cite as fontes do contexto quando relevante
        5. Se houver informações conflitantes, explique as diferentes perspectivas
        
        Contexto fornecido:
        {context}"""
        
        # Histórico do chat
        self.messages: List[Dict[str, Any]] = []
        
    def _format_chat_history(self) -> List[HumanMessage | AIMessage]:
        """
        Formata o histórico do chat para o formato do LangChain
        
        Returns:
            Lista de mensagens formatadas
        """
        formatted_messages = []
        for msg in self.messages[-5:]:  # Últimas 5 mensagens
            if msg["role"] == "human":
                formatted_messages.append(HumanMessage(content=msg["content"]))
            else:
                formatted_messages.append(AIMessage(content=msg["content"]))
        return formatted_messages
        
    def _get_relevant_context(self, query: str, k: int = 3) -> str:
        """
        Recupera contexto relevante da base RAG
        
        Args:
            query: Pergunta do usuário
            k: Número de documentos a recuperar
            
        Returns:
            Contexto formatado
        """
        docs = self.rag.query(query, k=k)
        
        if not docs:
            return "Nenhum contexto relevante encontrado na base de conhecimento."
            
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('source', 'Desconhecida')
            context_parts.append(f"Documento {i} (Fonte: {source}):\n{doc.page_content}\n")
            
        return "\n".join(context_parts)
        
    async def chat(self, message: str, include_context: bool = True) -> str:
        """
        Processa uma mensagem do usuário e retorna a resposta
        
        Args:
            message: Mensagem do usuário
            include_context: Se deve incluir contexto do RAG
            
        Returns:
            Resposta do assistente
        """
        try:
            # Recupera contexto relevante
            context = self._get_relevant_context(message) if include_context else ""
            
            # Prepara as mensagens
            messages = [
                SystemMessage(content=self.system_template.format(context=context))
            ]
            messages.extend(self._format_chat_history())
            messages.append(HumanMessage(content=message))
            
            # Gera a resposta
            response = await self.chat_model.ainvoke(messages)
            response_text = response.content
            
            # Atualiza o histórico
            self.messages.append({
                "role": "human",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            self.messages.append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            })
            
            return response_text
            
        except Exception as e:
            error_msg = f"Erro ao processar mensagem: {str(e)}"
            print(error_msg)
            return error_msg
            
    def clear_history(self) -> None:
        """
        Limpa o histórico do chat
        """
        self.messages = []
        
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """
        Retorna o histórico do chat
        
        Returns:
            Lista com mensagens do histórico
        """
        return self.messages
