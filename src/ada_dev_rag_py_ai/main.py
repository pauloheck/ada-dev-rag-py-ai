"""
Módulo principal para execução do sistema RAG
"""
import os
from ada_dev_rag_py_ai.core import init_llm, init_rag, create_qa_chain
from ada_dev_rag_py_ai.image_analysis import analyze_image

def main():
    """
    Função principal que demonstra o funcionamento básico do sistema
    """
    try:
        # Inicializa o modelo e o sistema RAG
        print("\nInicializando o modelo LLM e o sistema RAG...")
        llm = init_llm()
        rag = init_rag()
        
        # Cria a chain de QA
        qa_chain = create_qa_chain(llm, rag)
        

        
        while True:
            print("\n=== Sistema RAG - Menu Principal ===\n")
            
            print("1. Carregamento de Documentos")
            print("   1. Carregar documentos de um diretório")
            print("   2. Carregar arquivo PDF")
            print("   3. Adicionar texto manualmente")
            print("   4. Carregar imagem")
            print("   5. Carregar diretório de imagens")
            
            print("\n2. Consulta e Visualização")
            print("   6. Fazer uma pergunta")
            print("   7. Listar documentos")
            print("   8. Visualizar conteúdo das fontes")
            
            print("\n3. Estatísticas e Gerenciamento")
            print("   9. Ver estatísticas")
            print("   10. Estatísticas detalhadas")
            print("   11. Remover documento")
            print("   12. Limpar base de dados")
            print("   13. Exportar documentos")
            
            print("\n0. Sair")
            print("\n" + "="*20)
            
            choice = input("\nEscolha uma opção: ")
            
            if choice == "0":
                print("\nEncerrando o programa...")
                break
            
            elif choice == "1":
                directory = input("\nDigite o caminho do diretório com os documentos: ")
                try:
                    print("\nAnalisando diretório...")
                    stats = rag.load_directory(directory)
                    
                    print("\nResumo do Carregamento:")
                    print("=" * 50)
                    print(f"Total de arquivos: {stats['total_files']}")
                    print(f"Arquivos processados com sucesso: {stats['processed_files']}")
                    print(f"Arquivos ignorados: {stats['skipped_files']}")
                    print(f"Arquivos com erro: {stats['failed_files']}")
                    
                    if stats['errors']:
                        print("\nErros encontrados:")
                        for error in stats['errors']:
                            print(f"- {error}")
                    
                    if stats['processed_files'] > 0:
                        print("\nCarregamento concluído com sucesso!")
                    else:
                        print("\nNenhum arquivo foi processado com sucesso.")
                        
                except FileNotFoundError as e:
                    print(f"\nErro: {e}")
                    print("Verifique se o caminho do diretório está correto.")
                except NotADirectoryError as e:
                    print(f"\nErro: {e}")
                    print("O caminho fornecido deve ser um diretório válido.")
                except ValueError as e:
                    print(f"\nErro: {e}")
                    print("Certifique-se de que o diretório contém arquivos .txt ou .pdf válidos.")
                except Exception as e:
                    print(f"\nErro inesperado ao carregar documentos: {e}")
                
            elif choice == "2":
                pdf_path = input("\nDigite o caminho do arquivo PDF: ")
                print("\nCarregando PDF...")
                rag.load_pdf(pdf_path)
                print("PDF carregado com sucesso!")
                
            elif choice == "3":
                text = input("\nDigite ou cole o texto a ser adicionado:\n")
                print("\nProcessando texto...")
                rag.add_texts([text])
                print("Texto adicionado com sucesso!")
                
            elif choice == "4":
                image_path = input("\nDigite o caminho do arquivo de imagem: ")
                print("\nCarregando imagem...")
                document = rag.carregar_imagem(image_path)
                if document:
                    print("Imagem carregada com sucesso!")
                else:
                    print("Erro ao carregar a imagem.")
                
            elif choice == "5":
                directory = input("\nDigite o caminho do diretório de imagens: ")
                print("\nProcessando diretório de imagens...")
                stats = rag.load_diagram_directory(directory)
                print("\nProcessamento concluído!")
                
            elif choice == "6":
                question = input("\nFaça sua pergunta: ")
                print("\nProcessando sua pergunta...")
                result = qa_chain.invoke({"input": question})
                
                print("\n" + "="*50)
                # O resultado é uma string direta
                print("Resposta:", result)
                print("\nFontes utilizadas:")
                # As fontes não estão disponíveis no novo formato da chain
                print("Nenhuma fonte disponível.")
                
            elif choice == "7":
                print("\nListando documentos na base:")
                print("=" * 50)
                docs = rag.list_documents()
                if not docs:
                    print("Nenhum documento encontrado na base.")
                else:
                    for i, doc in enumerate(docs, 1):
                        print(f"\nDocumento {i}:")
                        if hasattr(doc, 'metadata'):
                            print(f"Fonte: {doc.metadata['source']}")
                            print(f"Metadados: {doc.metadata}")
                        print(f"Conteúdo: {doc.page_content[:200]}...")
                
            elif choice == "8":
                source = input("\nDigite o caminho da fonte (deixe em branco para todas): ")
                content = rag.get_source_content(source if source else None)
                if not content:
                    print("Nenhum conteúdo encontrado.")
                else:
                    print("\nConteúdo das fontes:")
                    print("=" * 50)
                    for doc in content:
                        print("-" * 30)
                        if "source" in doc:
                            print(f"Fonte: {doc['source']}")
                        print(f"Conteúdo:\n{doc['content'][:500]}...")
                
            elif choice == "9":
                stats = rag.get_collection_stats()
                print("\nEstatísticas da Base:")
                print("=" * 50)
                print(f"Total de documentos: {stats['total_documents']}")
                print(f"Diretório de persistência: {stats['persist_directory']}")
                
            elif choice == "10":
                stats = rag.get_detailed_stats()
                print("\nEstatísticas Detalhadas:")
                print("=" * 50)
                print(f"Total de documentos: {stats['total_documents']}")
                print(f"Diretório de persistência: {stats['persist_directory']}")
                if stats['total_documents'] > 0:
                    print(f"\nEstatísticas de conteúdo:")
                    print(f"Tamanho total: {stats['total_content_size']} caracteres")
                    print(f"Tamanho médio: {stats['average_content_size']:.2f} caracteres")
                    print(f"Menor documento: {stats['min_content_size']} caracteres")
                    print(f"Maior documento: {stats['max_content_size']} caracteres")
                
            elif choice == "11":
                doc_id = input("\nDigite o ID do documento a ser removido: ")
                if rag.delete_document(doc_id):
                    print("Documento removido com sucesso!")
                else:
                    print("Erro ao remover documento.")
                
            elif choice == "12":
                confirm = input("\nTem certeza que deseja limpar toda a base? (s/n): ")
                if confirm.lower() == 's':
                    if rag.clear_collection():
                        print("Base de dados limpa com sucesso!")
                    else:
                        print("Erro ao limpar a base de dados.")
                else:
                    print("Operação cancelada.")
                
            elif choice == "13":
                export_dir = input("\nDigite o diretório para exportar os documentos: ")
                if rag.export_collection(export_dir):
                    print("Documentos exportados com sucesso!")
                else:
                    print("Erro ao exportar documentos.")
                    
            else:
                print("\nOpção inválida. Por favor, escolha uma opção válida.")
                
    except Exception as e:
        print(f"\nErro fatal: {e}")
        print("O programa será encerrado.")
        raise

if __name__ == "__main__":
    main()
