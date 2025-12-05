"""
Cliente Redis para cache e filas
"""
import logging
from typing import Optional, Any, Dict, List
import json
import redis.asyncio as redis
from redis.asyncio import Redis

from src.config.config import config

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Cliente Redis para gerenciar cache e filas
    """
    
    def __init__(self):
        self._client: Optional[Redis] = None
        self._connection_url = config.redis.connection_url
    
    async def connect(self):
        """Conecta ao Redis"""
        try:
            self._client = await redis.from_url(
                self._connection_url,
                decode_responses=config.redis.decode_responses,
                encoding="utf-8"
            )
            # Testar conexão
            await self._client.ping()
            logger.info("Conectado ao Redis com sucesso")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {e}")
            raise
    
    async def disconnect(self):
        """Desconecta do Redis"""
        if self._client:
            await self._client.close()
            logger.info("Desconectado do Redis")
    
    @property
    def client(self) -> Redis:
        """Retorna cliente Redis"""
        if not self._client:
            raise RuntimeError("Redis não está conectado. Chame connect() primeiro.")
        return self._client
    
    # Métodos de Cache
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache"""
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Erro ao obter chave {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Define valor no cache com TTL opcional (segundos)"""
        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)
        except Exception as e:
            logger.error(f"Erro ao definir chave {key}: {e}")
    
    async def delete(self, key: str):
        """Remove chave do cache"""
        try:
            await self.client.delete(key)
        except Exception as e:
            logger.error(f"Erro ao deletar chave {key}: {e}")
    
    async def exists(self, key: str) -> bool:
        """Verifica se chave existe"""
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Erro ao verificar chave {key}: {e}")
            return False
    
    # Métodos de Fila
    
    async def enqueue(self, queue_name: str, data: Dict[str, Any]):
        """Adiciona item à fila"""
        try:
            serialized = json.dumps(data, default=str)
            await self.client.lpush(queue_name, serialized)
        except Exception as e:
            logger.error(f"Erro ao adicionar à fila {queue_name}: {e}")
            raise
    
    async def dequeue(self, queue_name: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Remove e retorna item da fila (blocking)"""
        try:
            result = await self.client.brpop(queue_name, timeout=timeout)
            if result:
                _, value = result
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Erro ao remover da fila {queue_name}: {e}")
            return None
    
    async def queue_length(self, queue_name: str) -> int:
        """Retorna tamanho da fila"""
        try:
            return await self.client.llen(queue_name)
        except Exception as e:
            logger.error(f"Erro ao obter tamanho da fila {queue_name}: {e}")
            return 0
    
    # Métodos de Hash (útil para estruturas complexas)
    
    async def hset(self, key: str, field: str, value: Any):
        """Define campo em hash"""
        try:
            serialized = json.dumps(value, default=str)
            await self.client.hset(key, field, serialized)
        except Exception as e:
            logger.error(f"Erro ao definir hash {key}.{field}: {e}")
    
    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Obtém campo de hash"""
        try:
            value = await self.client.hget(key, field)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Erro ao obter hash {key}.{field}: {e}")
            return None
    
    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Obtém todos os campos de hash"""
        try:
            data = await self.client.hgetall(key)
            return {k: json.loads(v) for k, v in data.items()}
        except Exception as e:
            logger.error(f"Erro ao obter hash completo {key}: {e}")
            return {}
    
    async def hdel(self, key: str, field: str):
        """Remove campo de hash"""
        try:
            await self.client.hdel(key, field)
        except Exception as e:
            logger.error(f"Erro ao deletar hash {key}.{field}: {e}")


# Instância global do cliente Redis
redis_client = RedisClient()

