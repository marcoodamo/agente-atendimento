"""
Serviço de geração de embeddings
"""
import logging
from typing import List
import asyncio

from src.config.config import config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Serviço para gerar embeddings de texto
    """
    
    def __init__(self):
        self.provider = config.embedding.provider.lower()
        self.model = config.embedding.model
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa o cliente de embeddings"""
        if self.provider == "openai":
            from openai import OpenAI
            if not config.embedding.openai_api_key:
                raise ValueError("OPENAI_API_KEY não configurada para embeddings")
            self.client = OpenAI(api_key=config.embedding.openai_api_key)
        elif self.provider == "sentence-transformers":
            # Usar modelo local
            try:
                from sentence_transformers import SentenceTransformer
                self.model_local = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                self.client = None
            except ImportError:
                logger.warning("sentence-transformers não instalado, usando OpenAI")
                self.provider = "openai"
                from openai import OpenAI
                self.client = OpenAI(api_key=config.embedding.openai_api_key)
        else:
            raise ValueError(f"Provedor de embeddings não suportado: {self.provider}")
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Gera embedding para um texto
        
        Args:
            text: Texto a ser vetorizado
            
        Returns:
            Lista de floats representando o embedding
        """
        try:
            if self.provider == "openai":
                # OpenAI API é síncrona, então executamos em thread
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.embeddings.create(
                        model=self.model,
                        input=text
                    )
                )
                return response.data[0].embedding
            elif self.provider == "sentence-transformers":
                # Modelo local
                loop = asyncio.get_event_loop()
                embedding = await loop.run_in_executor(
                    None,
                    lambda: self.model_local.encode(text, convert_to_numpy=True)
                )
                return embedding.tolist()
            else:
                raise ValueError(f"Provedor não suportado: {self.provider}")
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Gera embeddings para múltiplos textos
        
        Args:
            texts: Lista de textos
            
        Returns:
            Lista de embeddings
        """
        if self.provider == "openai":
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.embeddings.create(
                    model=self.model,
                    input=texts
                )
            )
            return [item.embedding for item in response.data]
        elif self.provider == "sentence-transformers":
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model_local.encode(texts, convert_to_numpy=True)
            )
            return embeddings.tolist()
        else:
            # Fallback: processar um por um
            return [await self.embed_text(text) for text in texts]

