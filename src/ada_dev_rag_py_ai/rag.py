"""
Módulo principal do sistema RAG para processamento de documentos e diagramas
"""
import os
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from .diagram_processor import DiagramProcessor

class RAG:
    def __init__(self, persist_directory: str = "chroma_db"):
        """
        Inicializa o sistema RAG
        
        Args:
            persist_directory: Diretório para persistir a base vetorial
        """
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings()
        self.diagram_processor = DiagramProcessor()
        
        # Cria ou carrega a base vetorial
        if os.path.exists(persist_directory):
            self.vectordb = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings
            )
        else:
            self.vectordb = Chroma(
                embedding_function=self.embeddings,
                persist_directory=persist_directory
            )
    
    def load_diagram(self, image_path: str) -> Optional[Document]:
        """
        Carrega e processa um diagrama
        
        Args:
            image_path: Caminho para o arquivo PNG
            
        Returns:
            Documento processado ou None se houver erro
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {image_path}")
                
            if not image_path.lower().endswith('.png'):
                raise ValueError("Arquivo deve ser PNG")
            
            # Processa o diagrama
            document = self.diagram_processor.process_diagram(image_path)
            
            # Adiciona à base vetorial
            self.vectordb.add_documents([document])
            self.vectordb.persist()
            
            return document
            
        except Exception as e:
            print(f"Erro ao carregar diagrama {image_path}: {str(e)}")
            return None
    
    def load_diagram_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Carrega e processa todos os diagramas PNG de um diretório
        
        Args:
            directory_path: Caminho para o diretório com as imagens
            
        Returns:
            Dicionário com estatísticas do processamento
        """
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Diretório não encontrado: {directory_path}")
        
        stats = {
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "skipped_files": 0,
            "errors": []
        }
        
        # Lista todos os arquivos PNG
        for filename in os.listdir(directory_path):
            if filename.lower().endswith('.png'):
                stats["total_files"] += 1
                image_path = os.path.join(directory_path, filename)
                
                try:
                    document = self.load_diagram(image_path)
                    if document:
                        if document.metadata.get("status") == "success":
                            stats["processed_files"] += 1
                            print(f"Processado com sucesso: {filename}")
                            print(f"Elementos detectados: {document.metadata.get('num_elements', 0)}")
                            print(f"Tipos: {document.metadata.get('element_types_str', '')}")
                        else:
                            stats["failed_files"] += 1
                            error = document.metadata.get("error_message", "Erro desconhecido")
                            stats["errors"].append(f"{filename}: {error}")
                            print(f"Falha ao processar: {filename}")
                            print(f"Erro: {error}")
                    else:
                        stats["failed_files"] += 1
                        stats["errors"].append(f"{filename}: Erro no processamento")
                        
                except Exception as e:
                    stats["failed_files"] += 1
                    stats["errors"].append(f"{filename}: {str(e)}")
                    print(f"Erro ao processar {filename}: {str(e)}")
            else:
                stats["skipped_files"] += 1
        
        # Persiste a base vetorial
        self.vectordb.persist()
        
        print("\nResumo do processamento:")
        print(f"Total de arquivos: {stats['total_files']}")
        print(f"Processados com sucesso: {stats['processed_files']}")
        print(f"Falhas: {stats['failed_files']}")
        print(f"Ignorados (não PNG): {stats['skipped_files']}")
        
        if stats["errors"]:
            print("\nErros encontrados:")
            for error in stats["errors"]:
                print(f"- {error}")
        
        return stats
    
    def load_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Carrega todos os documentos de um diretório
        
        Args:
            directory_path: Caminho para o diretório com os documentos
            
        Returns:
            Dicionário com estatísticas do processamento
        """
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Diretório não encontrado: {directory_path}")
        
        stats = {
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "skipped_files": 0,
            "errors": []
        }
        
        # Lista todos os arquivos
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            
            if not os.path.isfile(file_path):
                continue
                
            stats["total_files"] += 1
            
            try:
                # Processa arquivos de texto e PDF
                if filename.lower().endswith(('.txt', '.md')):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Cria o documento
                    doc = Document(
                        page_content=content,
                        metadata={
                            'source': file_path,
                            'filename': filename,
                            'type': 'text'
                        }
                    )
                    
                    # Adiciona à base vetorial
                    self.vectordb.add_documents([doc])
                    stats["processed_files"] += 1
                    print(f"Processado com sucesso: {filename}")
                    
                elif filename.lower().endswith('.pdf'):
                    from langchain_community.document_loaders import PyPDFLoader
                    
                    # Carrega o PDF
                    loader = PyPDFLoader(file_path)
                    documents = loader.load()
                    
                    # Adiciona metadados extras
                    for doc in documents:
                        doc.metadata.update({
                            'filename': filename,
                            'type': 'pdf'
                        })
                    
                    # Adiciona à base vetorial
                    self.vectordb.add_documents(documents)
                    stats["processed_files"] += 1
                    print(f"Processado com sucesso: {filename} ({len(documents)} páginas)")
                    
                else:
                    stats["skipped_files"] += 1
                    print(f"Arquivo ignorado (formato não suportado): {filename}")
                    
            except Exception as e:
                stats["failed_files"] += 1
                error_msg = f"Erro ao processar {filename}: {str(e)}"
                stats["errors"].append(error_msg)
                print(error_msg)
        
        # Persiste as mudanças
        self.vectordb.persist()
        
        return stats

    def load_pdf(self, pdf_path: str) -> None:
        """
        Carrega um arquivo PDF
        
        Args:
            pdf_path: Caminho para o arquivo PDF
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")
            
        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError("O arquivo deve ser um PDF")
            
        try:
            from langchain_community.document_loaders import PyPDFLoader
            
            # Carrega o PDF
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # Adiciona metadados extras
            filename = os.path.basename(pdf_path)
            for doc in documents:
                doc.metadata.update({
                    'filename': filename,
                    'source': pdf_path,
                    'type': 'pdf'
                })
            
            # Adiciona à base vetorial
            self.vectordb.add_documents(documents)
            self.vectordb.persist()
            
            print(f"\nPDF processado com sucesso:")
            print(f"- Arquivo: {filename}")
            print(f"- Páginas processadas: {len(documents)}")
            
        except Exception as e:
            raise Exception(f"Erro ao processar o PDF: {str(e)}")

    def list_documents(self) -> List[Document]:
        """
        Lista todos os documentos armazenados na base vetorial
        
        Returns:
            Lista de documentos armazenados
        """
        results = self.vectordb.get()
        documents = []
        
        if results and len(results.get('documents', [])) > 0:
            for i, text in enumerate(results['documents']):
                metadata = results['metadatas'][i] if 'metadatas' in results else {}
                doc = Document(page_content=text, metadata=metadata)
                documents.append(doc)
                
        return documents

    def query(self, query: str, k: int = 3) -> List[Document]:
        """
        Consulta a base vetorial
        
        Args:
            query: Consulta em linguagem natural
            k: Número de documentos similares a retornar
            
        Returns:
            Lista de documentos similares
        """
        return self.vectordb.similarity_search(query, k=k)
