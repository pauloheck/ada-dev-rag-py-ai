"""
Script para processar diagramas usando OpenCV
"""
import os
from src.ada_dev_rag_py_ai.diagram_processor import DiagramProcessor

def main():
    # Diretório com as imagens
    image_dir = "C:\\rag\\image"
    
    if not os.path.exists(image_dir):
        print(f"Diretório não encontrado: {image_dir}")
        return
    
    # Inicializa o processador
    processor = DiagramProcessor()
    
    # Lista arquivos PNG
    png_files = [f for f in os.listdir(image_dir) if f.lower().endswith('.png')]
    
    if not png_files:
        print("Nenhum arquivo PNG encontrado no diretório.")
        return
    
    print(f"Encontrados {len(png_files)} arquivos PNG.")
    
    # Processa cada imagem
    for filename in png_files:
        image_path = os.path.join(image_dir, filename)
        print(f"\nProcessando {filename}...")
        
        try:
            # Processa o diagrama
            document = processor.process_diagram(image_path)
            
            # Mostra resultados
            if document.metadata["status"] == "success":
                print("✓ Sucesso!")
                print(f"Elementos detectados: {document.metadata['num_elements']}")
                print(f"Tipos: {document.metadata['element_types_str']}")
                print("\nDescrição:")
                print(document.page_content)
            else:
                print("✗ Falha!")
                print(f"Erro: {document.metadata.get('error_message', 'Erro desconhecido')}")
                
        except Exception as e:
            print(f"✗ Erro ao processar imagem: {str(e)}")

if __name__ == "__main__":
    main()
