"""
Módulo para gerenciamento de embeddings multimodais
"""
from typing import List, Union, Dict, Any
import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings

class MultimodalEmbeddings(Embeddings):
    """
    Classe para geração de embeddings multimodais usando CLIP para imagens
    e OpenAI para texto
    """
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Inicializa os modelos de embeddings
        
        Args:
            model_name: Nome do modelo CLIP a ser usado
        """
        self.text_embeddings = OpenAIEmbeddings()
        self.clip_model = CLIPModel.from_pretrained(model_name)
        self.clip_processor = CLIPProcessor.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.clip_model.to(self.device)
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Gera embeddings para uma lista de textos
        
        Args:
            texts: Lista de textos para gerar embeddings
            
        Returns:
            Lista de embeddings
        """
        return self.text_embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """
        Gera embedding para uma query de texto
        
        Args:
            text: Texto da query
            
        Returns:
            Embedding da query
        """
        return self.text_embeddings.embed_query(text)
    
    def embed_image(self, image: Union[str, Image.Image]) -> List[float]:
        """
        Gera embedding para uma imagem usando CLIP
        
        Args:
            image: Caminho da imagem ou objeto PIL.Image
            
        Returns:
            Embedding da imagem
        """
        if isinstance(image, str):
            image = Image.open(image)
            
        inputs = self.clip_processor(images=image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            image_features = self.clip_model.get_image_features(**inputs)
            
        # Normalize e converte para lista
        image_embedding = image_features.cpu().numpy()[0]
        image_embedding = image_embedding / np.linalg.norm(image_embedding)
        
        return image_embedding.tolist()
    
    def combine_embeddings(self, text_embedding: List[float], image_embedding: List[float], 
                          weight_text: float = 0.5) -> List[float]:
        """
        Combina embeddings de texto e imagem
        
        Args:
            text_embedding: Embedding do texto
            image_embedding: Embedding da imagem
            weight_text: Peso do embedding de texto (0-1)
            
        Returns:
            Embedding combinado
        """
        weight_image = 1 - weight_text
        combined = np.array(text_embedding) * weight_text + np.array(image_embedding) * weight_image
        combined = combined / np.linalg.norm(combined)
        return combined.tolist()
    
    def get_content_type(self, content: Union[str, Image.Image, Dict[str, Any]]) -> str:
        """
        Determina o tipo de conteúdo
        
        Args:
            content: Conteúdo a ser analisado
            
        Returns:
            Tipo do conteúdo ('text', 'image' ou 'multimodal')
        """
        if isinstance(content, str):
            return 'text'
        elif isinstance(content, Image.Image):
            return 'image'
        elif isinstance(content, dict) and 'text' in content and 'image' in content:
            return 'multimodal'
        else:
            raise ValueError("Tipo de conteúdo não suportado")
