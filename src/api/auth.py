"""
Sistema de autenticação via API Key
"""
import logging
from typing import Optional
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from fastapi.security.api_key import APIKey

from src.config.config import config

logger = logging.getLogger(__name__)

# Header esperado para API Key
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyAuth:
    """Gerenciador de autenticação via API Key"""
    
    def __init__(self):
        self.api_key = config.api.api_key
        self.enable_auth = config.api.enable_auth
    
    async def verify_api_key(
        self,
        api_key: Optional[str] = Security(API_KEY_HEADER)
    ) -> str:
        """
        Verifica se a API Key fornecida é válida
        
        Args:
            api_key: API Key do header X-API-Key
            
        Returns:
            API Key válida
            
        Raises:
            HTTPException: Se API Key inválida ou ausente
        """
        if not self.enable_auth:
            # Autenticação desabilitada (modo desenvolvimento)
            return "dev_mode"
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key não fornecida. Inclua o header 'X-API-Key'.",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        if api_key != self.api_key:
            logger.warning(f"Tentativa de acesso com API Key inválida")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API Key inválida",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        return api_key


# Instância global do autenticador
api_key_auth = APIKeyAuth()

