"""
Módulo responsável pelo processamento e interpretação de diagramas em imagens PNG
"""
import os
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from PIL import Image
from dataclasses import dataclass
from langchain_core.documents import Document

@dataclass
class DiagramElement:
    """Classe para representar elementos detectados no diagrama"""
    type: str
    confidence: float
    bbox: tuple  # (x1, y1, x2, y2)
    text: Optional[str] = None
    relationships: List[str] = None

class DiagramProcessor:
    def __init__(self):
        """Inicializa o processador de diagramas"""
        pass
        
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Pré-processa a imagem para melhorar a detecção
        
        Args:
            image_path: Caminho para a imagem PNG
            
        Returns:
            Array NumPy da imagem processada
        """
        # Carrega e converte para RGB
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Não foi possível carregar a imagem: {image_path}")
            
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Converte para escala de cinza
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Aplica threshold adaptativo
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2
        )
        
        # Remove ruído
        kernel = np.ones((3,3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        return binary
    
    def detect_elements(self, image_path: str) -> List[DiagramElement]:
        """
        Detecta elementos no diagrama usando contornos
        
        Args:
            image_path: Caminho para a imagem PNG
            
        Returns:
            Lista de elementos detectados
        """
        try:
            # Pré-processa a imagem
            binary = self.preprocess_image(image_path)
            
            # Encontra contornos
            contours, _ = cv2.findContours(
                binary,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            elements = []
            min_area = 100  # Área mínima para considerar um contorno
            
            # Processa cada contorno
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < min_area:
                    continue
                
                # Obtém o retângulo delimitador
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calcula a confiança baseada na área
                confidence = min(area / 10000, 1.0)
                
                # Detecta o tipo baseado na forma
                approx = cv2.approxPolyDP(
                    contour,
                    0.04 * cv2.arcLength(contour, True),
                    True
                )
                
                num_vertices = len(approx)
                aspect_ratio = float(w) / h if h > 0 else 0
                
                # Classifica a forma
                if num_vertices == 4:
                    if 0.95 <= aspect_ratio <= 1.05:
                        element_type = "box"
                    else:
                        element_type = "rectangle"
                elif num_vertices == 3:
                    element_type = "triangle"
                elif num_vertices > 8:
                    element_type = "circle"
                else:
                    element_type = "shape"
                
                element = DiagramElement(
                    type=element_type,
                    confidence=confidence,
                    bbox=(x, y, x+w, y+h)
                )
                elements.append(element)
            
            print(f"Detectados {len(elements)} elementos no diagrama")
            for elem in elements:
                print(f"- Tipo: {elem.type}, Confiança: {elem.confidence:.2f}")
            
            return elements
            
        except Exception as e:
            print(f"Erro durante a detecção de elementos: {str(e)}")
            raise
    
    def process_diagram(self, image_path: str) -> Document:
        """
        Processa um diagrama e retorna um documento com sua interpretação
        
        Args:
            image_path: Caminho para a imagem PNG
            
        Returns:
            Documento com a interpretação do diagrama
        """
        try:
            print(f"\nProcessando imagem: {image_path}")
            
            # Detecta elementos
            elements = self.detect_elements(image_path)
            
            if not elements:
                return Document(
                    page_content="Nenhum elemento foi detectado no diagrama.",
                    metadata={
                        "source": image_path,
                        "type": "diagram",
                        "num_elements": 0,
                        "element_types_str": "",
                        "status": "no_elements_detected"
                    }
                )
            
            # Gera descrição dos elementos
            element_types = list(set(e.type for e in elements))
            element_types_str = ", ".join(element_types)
            
            description = f"Diagrama contendo {len(elements)} elementos:\n"
            for element_type in element_types:
                count = sum(1 for e in elements if e.type == element_type)
                description += f"- {count} {element_type}(s)\n"
            
            # Analisa relações espaciais
            for i, elem1 in enumerate(elements):
                for elem2 in elements[i+1:]:
                    # Verifica sobreposição horizontal
                    if (elem1.bbox[0] < elem2.bbox[2] and 
                        elem2.bbox[0] < elem1.bbox[2]):
                        # elem1 está acima de elem2
                        if elem1.bbox[3] < elem2.bbox[1]:
                            description += f"- {elem1.type} está acima de {elem2.type}\n"
                        # elem1 está abaixo de elem2
                        elif elem1.bbox[1] > elem2.bbox[3]:
                            description += f"- {elem1.type} está abaixo de {elem2.type}\n"
                    
                    # Verifica sobreposição vertical
                    if (elem1.bbox[1] < elem2.bbox[3] and 
                        elem2.bbox[1] < elem1.bbox[3]):
                        # elem1 está à esquerda de elem2
                        if elem1.bbox[2] < elem2.bbox[0]:
                            description += f"- {elem1.type} está à esquerda de {elem2.type}\n"
                        # elem1 está à direita de elem2
                        elif elem1.bbox[0] > elem2.bbox[2]:
                            description += f"- {elem1.type} está à direita de {elem2.type}\n"
            
            return Document(
                page_content=description,
                metadata={
                    "source": image_path,
                    "type": "diagram",
                    "num_elements": len(elements),
                    "element_types_str": element_types_str,
                    "status": "success"
                }
            )
            
        except Exception as e:
            error_msg = f"Erro ao processar diagrama: {str(e)}"
            print(error_msg)
            
            return Document(
                page_content=error_msg,
                metadata={
                    "source": image_path,
                    "type": "diagram",
                    "status": "error",
                    "error_message": str(e),
                    "num_elements": 0,
                    "element_types_str": ""
                }
            )
