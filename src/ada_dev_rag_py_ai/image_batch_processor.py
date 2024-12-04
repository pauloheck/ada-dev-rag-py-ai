"""
Módulo para processamento em lote de imagens com cache
"""
import os
from typing import List, Dict, Optional
from pathlib import Path
import torch
from PIL import Image
import hashlib
import json
from datetime import datetime, timedelta
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import logging

class ImageBatchProcessor:
    def __init__(
        self,
        cache_dir: str = ".image_cache",
        cache_ttl: int = 24,  # horas
        batch_size: int = 4,
        max_workers: int = 4
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_ttl = timedelta(hours=cache_ttl)
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)

    def _get_image_hash(self, image_path: str) -> str:
        """Gera um hash único para a imagem baseado em seu conteúdo."""
        with open(image_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def _get_cache_path(self, image_hash: str) -> Path:
        """Retorna o caminho do arquivo de cache para um hash de imagem."""
        return self.cache_dir / f"{image_hash}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Verifica se o cache ainda é válido baseado no TTL."""
        if not cache_path.exists():
            return False
        
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime < self.cache_ttl

    @lru_cache(maxsize=100)
    def _get_cached_result(self, image_path: str) -> Optional[Dict]:
        """Recupera resultado do cache se disponível e válido."""
        image_hash = self._get_image_hash(image_path)
        cache_path = self._get_cache_path(image_hash)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Erro ao ler cache: {e}")
                return None
        return None

    def _save_to_cache(self, image_path: str, result: Dict):
        """Salva o resultado da análise no cache."""
        try:
            image_hash = self._get_image_hash(image_path)
            cache_path = self._get_cache_path(image_hash)
            
            with open(cache_path, "w") as f:
                json.dump(result, f)
        except Exception as e:
            self.logger.error(f"Erro ao salvar cache: {e}")

    def _process_single_image(self, image_path: str) -> Dict:
        """Processa uma única imagem, usando cache se disponível."""
        # Tenta recuperar do cache primeiro
        cached_result = self._get_cached_result(image_path)
        if cached_result:
            self.logger.info(f"Cache hit para {image_path}")
            return cached_result

        # Se não está em cache, processa a imagem
        try:
            from .image_analysis import analyze_image
            result = analyze_image(image_path)
            
            # Salva no cache
            self._save_to_cache(image_path, result)
            
            return result
        except Exception as e:
            self.logger.error(f"Erro ao processar imagem {image_path}: {e}")
            return {"error": str(e)}

    def process_batch(self, image_paths: List[str]) -> List[Dict]:
        """
        Processa um lote de imagens em paralelo, utilizando cache quando possível.
        
        Args:
            image_paths: Lista de caminhos das imagens para processar
            
        Returns:
            Lista de resultados de análise para cada imagem
        """
        self.logger.info(f"Iniciando processamento em lote de {len(image_paths)} imagens")
        
        # Divide em lotes do tamanho especificado
        batches = [
            image_paths[i:i + self.batch_size]
            for i in range(0, len(image_paths), self.batch_size)
        ]
        
        all_results = []
        
        # Processa cada lote
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for batch in batches:
                # Submete cada imagem do lote para processamento paralelo
                future_to_path = {
                    executor.submit(self._process_single_image, path): path
                    for path in batch
                }
                
                # Coleta os resultados mantendo a ordem
                batch_results = []
                for future in future_to_path:
                    path = future_to_path[future]
                    try:
                        result = future.result()
                        batch_results.append({
                            "path": path,
                            "result": result
                        })
                    except Exception as e:
                        self.logger.error(f"Erro ao processar {path}: {e}")
                        batch_results.append({
                            "path": path,
                            "error": str(e)
                        })
                
                all_results.extend(batch_results)
        
        self.logger.info(f"Processamento em lote concluído")
        return all_results

    def clear_cache(self, older_than: Optional[int] = None):
        """
        Limpa o cache de resultados.
        
        Args:
            older_than: Se especificado, remove apenas entradas mais antigas que X horas
        """
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                if older_than is not None:
                    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if datetime.now() - mtime < timedelta(hours=older_than):
                        continue
                cache_file.unlink()
            self.logger.info("Cache limpo com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao limpar cache: {e}")
