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
