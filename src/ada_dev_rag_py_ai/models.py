"""
Modelos de dados para a API
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class QueryRequest(BaseModel):
    question: str
    
class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    
class TextDocument(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None
    
class CollectionStats(BaseModel):
    total_documents: int
    document_types: Dict[str, int]
    
class DetailedStats(BaseModel):
    total_documents: int
    document_types: Dict[str, int]
    sources: List[str]
    last_modified: str
    collection_name: str
    
class DocumentContent(BaseModel):
    source: str
    type: str
    content: str

class ChatMessage(BaseModel):
    """
    Modelo para mensagem do chat
    """
    content: str
    include_context: bool = True

class ChatResponse(BaseModel):
    """
    Modelo para resposta do chat
    """
    message: str
    success: bool

class ChatHistory(BaseModel):
    """
    Modelo para histórico do chat
    """
    history: List[Dict[str, Any]]
    success: bool
