from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import asyncio
from pathlib import Path
import aiofiles
import tempfile
import logging
import time
import uuid
import json
import traceback

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rag_api.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

from src.ada_dev_rag_py_ai.rag import RAG
from src.ada_dev_rag_py_ai.models import (
    QueryRequest, 
    QueryResponse, 
    TextDocument, 
    CollectionStats,
    DetailedStats,
    DocumentContent
)
from .image_batch_processor import ImageBatchProcessor

app = FastAPI(
    title="RAG System API",
    description="API para sistema de Retrieval Augmented Generation",
    version="0.1.0",
    debug=True
)

# Instância global do RAG
rag = RAG()
image_processor = ImageBatchProcessor()

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Realiza uma consulta aos documentos usando RAG.
    """
    logger.info("Received query request: %s", request.question)

    if not request.question.strip():
        logger.warning("Empty question received")
        raise HTTPException(status_code=400, detail="A pergunta não pode estar vazia.")
    try:
        result = await asyncio.to_thread(rag.query, request.question)
        logger.info("Query result: %s", result)

        # Assuming Document has attributes 'page_content' and 'metadata'
        answer = " ".join([doc.page_content for doc in result])  # Example extraction
        sources = [{'source': doc.metadata['source'], 'type': doc.metadata['type']} for doc in result]  # Example extraction

        response = QueryResponse(answer=answer, sources=sources)
        logger.info("Response: %s", response)
        return response
    except Exception as e:
        logger.error("Error during query: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/text")
async def add_text_document(document: TextDocument):
    """
    Adiciona um documento de texto à base de conhecimento.
    """
    logger.info("Received request to add text document: %s", document)
    if not document.content.strip():
        raise HTTPException(status_code=400, detail="O conteúdo do documento não pode estar vazio.")
    logger.info("Preparing to add document content to the knowledge base: %s", document.content)
    
    try:
        # Pass only the content as a list to add_texts
        success = await asyncio.to_thread(
            rag.add_texts,
            [document.content]  # Pass content as a list
        )
        logger.info("Document added successfully: %s", success)
        if not success:
            logger.error("Failed to add document to the knowledge base")
            raise HTTPException(status_code=500, detail="Falha ao adicionar documento")
        logger.info("Returning success response for document addition")
        return {"message": "Documento adicionado com sucesso"}
    except Exception as e:
        logger.error("Error adding document to the knowledge base: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/directory")
async def load_directory(directory: str):
    """
    Carrega documentos de um diretório com logs detalhados.
    """
    # Generate a unique trace ID for this request
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"[{trace_id}] Received request to load directory: {directory}")
    
    if not Path(directory).exists():
        logger.warning(f"[{trace_id}] Directory does not exist: {directory}")
        raise HTTPException(status_code=400, detail="O diretório não existe.")
    
    try:
        logger.info(f"[{trace_id}] Starting to load documents from directory: {directory}")
        load_start = time.time()
        stats = await asyncio.to_thread(rag.load_directory, directory)
        load_duration = time.time() - load_start
        
        logger.info(f"[{trace_id}] Directory load statistics: {json.dumps(stats, indent=2)}")
        logger.info(f"[{trace_id}] Directory loaded in {load_duration:.4f} seconds")

        if stats.get('failed_files', 0) > 0:
            logger.warning(f"[{trace_id}] Some files failed to load from directory: {directory}")

        total_duration = time.time() - start_time
        logger.info(f"[{trace_id}] Total directory load process completed in {total_duration:.4f} seconds")

        return {"message": "Diretório carregado com sucesso", "stats": stats}
    except Exception as e:
        logger.error(f"[{trace_id}] Error loading directory {directory}: {str(e)}")
        logger.error(f"[{trace_id}] Traceback: {traceback.format_exc()}")
        
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/image")
async def upload_image(file: UploadFile = File(...)):
    """
    Faz upload e processa uma imagem.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="O arquivo de imagem não pode estar vazio.")
    try:
        # Cria arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Processa imagem
        success = await asyncio.to_thread(rag.carregar_imagem, temp_path)
        
        # Remove arquivo temporário
        Path(temp_path).unlink()
        
        if not success:
            raise HTTPException(status_code=500, detail="Falha ao processar imagem")
        return {"message": "Imagem processada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/images/directory")
async def load_image_directory(directory: str):
    """
    Carrega e processa imagens de um diretório.
    """
    if not Path(directory).exists():
        raise HTTPException(status_code=400, detail="O diretório de imagens não existe.")
    try:
        success = await asyncio.to_thread(rag.load_diagram_directory, directory)
        if not success:
            raise HTTPException(status_code=500, detail="Falha ao carregar diretório de imagens")
        return {"message": "Diretório de imagens carregado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/basic", response_model=CollectionStats)
async def get_basic_stats():
    """
    Retorna estatísticas básicas da coleção com logs detalhados.
    """
    # Generate a unique trace ID for this request
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"[{trace_id}] Starting basic stats retrieval")
    
    try:
        # Log the start of stats collection with trace ID
        logger.debug(f"[{trace_id}] Preparing to collect collection statistics")
        
        # Measure the time taken to retrieve stats
        stats_start = time.time()
        raw_stats = await asyncio.to_thread(rag.get_collection_stats)
        stats_duration = time.time() - stats_start
        
        # Ensure document_types is present
        if 'document_types' not in raw_stats:
            # Attempt to derive document types from available information
            raw_stats['document_types'] = {
                'text': raw_stats.get('total_documents', 0),
                'image': 0,  # Add other types as needed
            }
        
        # Log performance and details
        logger.info(f"[{trace_id}] Basic stats retrieved successfully in {stats_duration:.4f} seconds")
        logger.debug(f"[{trace_id}] Stats details: {json.dumps(raw_stats, indent=2)}")
        
        # Log specific collection insights
        logger.info(f"[{trace_id}] Collection contains: "
                    f"{raw_stats.get('total_documents', 0)} documents, "
                    f"Document types: {raw_stats.get('document_types', {})}")
        
        total_duration = time.time() - start_time
        logger.info(f"[{trace_id}] Total stats retrieval process completed in {total_duration:.4f} seconds")
        
        return CollectionStats(
            total_documents=raw_stats.get('total_documents', 0),
            document_types=raw_stats.get('document_types', {})
        )
    
    except Exception as e:
        # Enhanced error logging
        logger.error(f"[{trace_id}] Error retrieving basic stats: {str(e)}")
        logger.error(f"[{trace_id}] Traceback: {traceback.format_exc()}")
        logger.error(f"[{trace_id}] Error occurred after {time.time() - start_time:.4f} seconds")
        
        # Include context about potential causes
        if not rag:
            logger.critical(f"[{trace_id}] RAG instance is not initialized")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao recuperar estatísticas: {str(e)}"
        )

@app.get("/stats/detailed", response_model=DetailedStats)
async def get_detailed_stats():
    """
    Retorna estatísticas detalhadas da coleção com logs abrangentes.
    """
    # Generate a unique trace ID for this request
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"[{trace_id}] Starting detailed stats retrieval")
    
    try:
        # Log the start of detailed stats collection
        logger.debug(f"[{trace_id}] Preparing to collect detailed collection statistics")
        
        # Measure the time taken to retrieve detailed stats
        stats_start = time.time()
        raw_stats = await asyncio.to_thread(rag.get_detailed_stats)
        stats_duration = time.time() - stats_start
        
        # Ensure all required fields are present
        if 'document_types' not in raw_stats:
            raw_stats['document_types'] = {
                'text': raw_stats.get('total_documents', 0),
                'image': 0,  # Add other types as needed
            }
        
        # Add default values for missing fields
        raw_stats.setdefault('sources', [])
        raw_stats.setdefault('last_modified', time.strftime("%Y-%m-%d %H:%M:%S"))
        raw_stats.setdefault('collection_name', 'default_collection')
        
        # Log performance and details
        logger.info(f"[{trace_id}] Detailed stats retrieved successfully in {stats_duration:.4f} seconds")
        logger.debug(f"[{trace_id}] Detailed stats: {json.dumps(raw_stats, indent=2)}")
        
        # Log specific collection insights
        logger.info(f"[{trace_id}] Detailed collection stats:")
        logger.info(f"[{trace_id}] - Total Documents: {raw_stats.get('total_documents', 0)}")
        logger.info(f"[{trace_id}] - Document Types: {raw_stats.get('document_types', {})}")
        logger.info(f"[{trace_id}] - Sources: {len(raw_stats.get('sources', []))} sources")
        logger.info(f"[{trace_id}] - Last Modified: {raw_stats.get('last_modified', 'N/A')}")
        logger.info(f"[{trace_id}] - Collection Name: {raw_stats.get('collection_name', 'N/A')}")
        
        total_duration = time.time() - start_time
        logger.info(f"[{trace_id}] Total detailed stats retrieval process completed in {total_duration:.4f} seconds")
        
        # Construct DetailedStats with all required fields
        return DetailedStats(
            total_documents=raw_stats.get('total_documents', 0),
            document_types=raw_stats.get('document_types', {}),
            sources=raw_stats.get('sources', []),
            last_modified=raw_stats.get('last_modified', time.strftime("%Y-%m-%d %H:%M:%S")),
            collection_name=raw_stats.get('collection_name', 'default_collection')
        )
    
    except Exception as e:
        # Enhanced error logging
        logger.error(f"[{trace_id}] Error retrieving detailed stats: {str(e)}")
        logger.error(f"[{trace_id}] Traceback: {traceback.format_exc()}")
        logger.error(f"[{trace_id}] Error occurred after {time.time() - start_time:.4f} seconds")
        
        # Include context about potential causes
        if not rag:
            logger.critical(f"[{trace_id}] RAG instance is not initialized")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao recuperar estatísticas detalhadas: {str(e)}"
        )

@app.get("/documents", response_model=List[DocumentContent])
async def get_documents(source: Optional[str] = None):
    """
    Lista todos os documentos ou documentos de uma fonte específica.
    """
    try:
        docs = await asyncio.to_thread(rag.get_source_content, source)
        return [DocumentContent(**doc) for doc in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/export")
async def export_collection(directory: str):
    """
    Exporta a coleção para um diretório.
    """
    if not Path(directory).exists():
        raise HTTPException(status_code=400, detail="O diretório para exportação não existe.")
    try:
        success = await asyncio.to_thread(rag.export_collection, directory)
        if not success:
            raise HTTPException(status_code=500, detail="Falha ao exportar coleção")
        return {"message": "Coleção exportada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents")
async def clear_collection():
    """
    Limpa toda a coleção com logs detalhados e rastreamento.
    """
    # Generate a unique trace ID for this request
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.warning(f"[{trace_id}] Iniciando processo de limpeza da coleção completa")
    
    try:
        # Log the start of collection clearing
        logger.debug(f"[{trace_id}] Preparando para limpar toda a coleção de documentos")
        
        # Retrieve current collection stats before clearing
        pre_clear_stats = await asyncio.to_thread(rag.get_collection_stats)
        pre_clear_document_count = pre_clear_stats.get('total_documents', 0)
        
        # Measure the time taken to clear the collection
        clear_start = time.time()
        await asyncio.to_thread(rag.clear_collection)  # Updated method name
        clear_duration = time.time() - clear_start
        
        # Log performance and details
        logger.info(f"[{trace_id}] Coleção limpa com sucesso em {clear_duration:.4f} segundos")
        logger.info(f"[{trace_id}] Documentos removidos: {pre_clear_document_count}")
        
        # Verify the collection is empty
        post_clear_stats = await asyncio.to_thread(rag.get_collection_stats)
        post_clear_document_count = post_clear_stats.get('total_documents', 0)
        
        logger.info(f"[{trace_id}] Verificação pós-limpeza: {post_clear_document_count} documentos restantes")
        
        total_duration = time.time() - start_time
        logger.info(f"[{trace_id}] Processo de limpeza da coleção concluído em {total_duration:.4f} segundos")
        
        return {
            "message": "Coleção limpa com sucesso", 
            "documents_removed": pre_clear_document_count,
            "duration": clear_duration
        }
    
    except Exception as e:
        # Enhanced error logging
        logger.error(f"[{trace_id}] Erro ao limpar coleção: {str(e)}")
        logger.error(f"[{trace_id}] Traceback: {traceback.format_exc()}")
        logger.error(f"[{trace_id}] Erro ocorreu após {time.time() - start_time:.4f} segundos")
        
        # Include context about potential causes
        if not rag:
            logger.critical(f"[{trace_id}] Instância RAG não inicializada")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Erro ao limpar coleção: {str(e)}"
        )

@app.delete("/documents/{source}")
async def remove_document(source: str):
    """
    Remove um documento específico da coleção.
    """
    if not source.strip():
        raise HTTPException(status_code=400, detail="A fonte do documento não pode estar vazia.")
    try:
        success = await asyncio.to_thread(rag.remover_documento, source)
        if not success:
            raise HTTPException(status_code=500, detail="Falha ao remover documento")
        return {"message": "Documento removido com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/images/batch")
async def process_image_batch(files: List[UploadFile] = File(...)):
    """Processa um lote de imagens em paralelo com cache."""
    temp_paths = []
    try:
        for file in files:
            temp_dir = Path("temp_uploads")
            temp_dir.mkdir(exist_ok=True)
            temp_path = temp_dir / f"{uuid.uuid4()}_{file.filename}"
            async with aiofiles.open(temp_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            temp_paths.append(str(temp_path))
        
        results = image_processor.process_batch(temp_paths)
        
        # Limpa arquivos temporários
        for path in temp_paths:
            Path(path).unlink(missing_ok=True)
        
        return {"results": results}
    except Exception as e:
        logger.error(f"Erro no processamento em lote: {e}")
        for path in temp_paths:
            Path(path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/images/cache")
async def clear_image_cache(older_than: Optional[int] = None):
    """Limpa o cache de processamento de imagens."""
    try:
        image_processor.clear_cache(older_than)
        return {"message": "Cache limpo com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
