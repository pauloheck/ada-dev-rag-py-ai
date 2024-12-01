"""
Módulo principal do sistema RAG para processamento de documentos e diagramas
"""
import os
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from .image_analysis import analyze_image
from datetime import datetime

class RAG:
    def __init__(self, persist_directory: str = "chroma_db"):
        """
        Inicializa o sistema RAG
        
        Args:
            persist_directory: Diretório para persistir a base vetorial
        """
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings()
        
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
            
            # Analisa a imagem usando image_analysis
            analysis_result = analyze_image(image_path)

            # Cria o documento com base no resultado da análise
            document = Document(
                page_content=analysis_result,
                metadata={
                    'source': image_path,
                    'filename': os.path.basename(image_path),
                    'type': 'image'
                }
            )

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
                        stats["processed_files"] += 1
                        print(f"Processado com sucesso: {filename}")
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

    def carregar_imagem(self, image_path: str) -> Optional[Document]:
        """
        Realiza o processo de análise da imagem e carrega o resultado no banco vetorial.
        
        Args:
            image_path: Caminho para o arquivo de imagem
        
        Returns:
            Documento processado ou None se houver erro
        """
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {image_path}")

            # Analisa a imagem usando image_analysis
            analysis_result = analyze_image(image_path)

            # Cria o documento com base no resultado da análise
            document = Document(
                page_content=analysis_result,
                metadata={
                    'source': image_path,
                    'filename': os.path.basename(image_path),
                    'type': 'image'
                }
            )

            # Adiciona o documento ao banco vetorial
            self.vectordb.add_documents([document])
            self.vectordb.persist()

            return document
        except Exception as e:
            print(f"Erro ao carregar imagem {image_path}: {str(e)}")
            return None

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

    def clear_collection(self) -> None:
        """
        Limpa toda a base vetorial de documentos.
        """
        # Obtém todos os IDs de documentos na coleção
        doc_ids = self.vectordb.get()["ids"]
        # Deleta os documentos usando os IDs
        self.vectordb.delete(ids=doc_ids)
        # Persiste as mudanças
        self.vectordb.persist()

    def export_collection(self, export_dir: str) -> bool:
        """
        Exporta todos os documentos da base vetorial para um diretório.
        
        Args:
            export_dir: Diretório onde os documentos serão exportados
            
        Returns:
            True se a exportação foi bem sucedida, False caso contrário
        """
        try:
            # Cria o diretório se não existir
            os.makedirs(export_dir, exist_ok=True)
            
            # Obtém todos os documentos
            docs = self.list_documents()
            if not docs:
                print("Nenhum documento para exportar.")
                return True
                
            # Exporta cada documento
            for i, doc in enumerate(docs, 1):
                # Define o nome do arquivo
                filename = f"documento_{i}.txt"
                if 'source' in doc.metadata:
                    base_name = os.path.basename(doc.metadata['source'])
                    name, _ = os.path.splitext(base_name)
                    filename = f"{name}_exported.txt"
                
                # Caminho completo do arquivo
                file_path = os.path.join(export_dir, filename)
                
                # Prepara o conteúdo
                content = [
                    "=== Documento Exportado ===",
                    f"ID: {i}",
                    "Metadados:",
                ]
                
                # Adiciona os metadados
                for key, value in doc.metadata.items():
                    content.append(f"- {key}: {value}")
                
                # Adiciona o conteúdo do documento
                content.extend([
                    "\nConteúdo:",
                    "=" * 50,
                    doc.page_content,
                    "=" * 50
                ])
                
                # Salva o arquivo
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(content))
                
                print(f"Exportado: {filename}")
            
            print(f"\nTodos os documentos foram exportados para: {export_dir}")
            return True
            
        except Exception as e:
            print(f"Erro ao exportar documentos: {str(e)}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas básicas da base vetorial.
        
        Returns:
            Dicionário com estatísticas básicas
        """
        try:
            # Obtém todos os documentos
            docs = self.list_documents()
            
            # Calcula estatísticas básicas
            stats = {
                "total_documents": len(docs),
                "persist_directory": self.persist_directory
            }
            
            return stats
            
        except Exception as e:
            print(f"Erro ao obter estatísticas: {str(e)}")
            return {
                "total_documents": 0,
                "persist_directory": self.persist_directory,
                "error": str(e)
            }
            
    def get_detailed_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas detalhadas da base vetorial.
        
        Returns:
            Dicionário com estatísticas detalhadas
        """
        try:
            # Obtém todos os documentos
            docs = self.list_documents()
            
            # Inicializa contadores
            total_docs = len(docs)
            total_size = 0
            min_size = float('inf')
            max_size = 0
            doc_types = {}
            
            # Analisa cada documento
            for doc in docs:
                # Tamanho do conteúdo
                content_size = len(doc.page_content)
                total_size += content_size
                min_size = min(min_size, content_size)
                max_size = max(max_size, content_size)
                
                # Contagem por tipo
                doc_type = doc.metadata.get('type', 'desconhecido')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            # Calcula estatísticas
            stats = {
                "total_documents": total_docs,
                "persist_directory": self.persist_directory,
                "documents_by_type": doc_types
            }
            
            # Adiciona estatísticas de tamanho se houver documentos
            if total_docs > 0:
                stats.update({
                    "total_content_size": total_size,
                    "average_content_size": total_size / total_docs,
                    "min_content_size": min_size,
                    "max_content_size": max_size
                })
            
            return stats
            
        except Exception as e:
            print(f"Erro ao obter estatísticas detalhadas: {str(e)}")
            return {
                "total_documents": 0,
                "persist_directory": self.persist_directory,
                "error": str(e)
            }

    def add_texts(self, texts: List[str]) -> bool:
        """
        Adiciona uma lista de textos à base vetorial.
        
        Args:
            texts: Lista de textos a serem adicionados
            
        Returns:
            True se os textos foram adicionados com sucesso, False caso contrário
        """
        try:
            # Cria documentos a partir dos textos
            documents = []
            for i, text in enumerate(texts, 1):
                doc = Document(
                    page_content=text,
                    metadata={
                        'source': f'texto_manual_{i}',
                        'type': 'texto',
                        'added_at': datetime.now().isoformat()
                    }
                )
                documents.append(doc)
            
            # Adiciona os documentos à base vetorial
            self.vectordb.add_documents(documents)
            self.vectordb.persist()
            
            print(f"{len(documents)} texto(s) adicionado(s) com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar textos: {str(e)}")
            return False

    def get_source_content(self, source: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Retorna o conteúdo dos documentos de uma fonte específica ou de todas as fontes.
        
        Args:
            source: Caminho da fonte específica ou None para todas as fontes
            
        Returns:
            Lista de dicionários com o conteúdo dos documentos
        """
        try:
            # Obtém todos os documentos
            docs = self.list_documents()
            if not docs:
                return []
                
            # Filtra por fonte se especificada
            if source:
                docs = [doc for doc in docs if doc.metadata.get('source') == source]
                
            # Formata o resultado
            result = []
            for doc in docs:
                result.append({
                    'source': doc.metadata.get('source', 'desconhecido'),
                    'type': doc.metadata.get('type', 'desconhecido'),
                    'content': doc.page_content
                })
                
            return result
            
        except Exception as e:
            print(f"Erro ao obter conteúdo: {str(e)}")
            return []
