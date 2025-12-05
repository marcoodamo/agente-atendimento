"""
Serviço de integração com Calendly API
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx

from src.config.config import config

logger = logging.getLogger(__name__)


class CalendlyService:
    """
    Serviço para interagir com Calendly API
    """
    
    def __init__(self):
        self.api_key = config.calendly.api_key
        self.base_url = config.calendly.base_url
        
        if not self.api_key:
            logger.warning("Calendly API key não configurada")
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers para requisições à API"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_available_times(
        self,
        event_type_uri: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém horários disponíveis para um tipo de evento
        
        Args:
            event_type_uri: URI do tipo de evento no Calendly
            start_time: Data/hora inicial da busca
            end_time: Data/hora final da busca
            
        Returns:
            Lista de slots disponíveis
        """
        try:
            url = f"{self.base_url}/api/v1/event_type_available_times"
            params = {
                "event_type": event_type_uri
            }
            
            if start_time:
                params["start_time"] = start_time.isoformat()
            if end_time:
                params["end_time"] = end_time.isoformat()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                return data.get("collection", [])
                
        except Exception as e:
            logger.error(f"Erro ao buscar horários disponíveis: {e}")
            return []
    
    async def create_event(
        self,
        event_type_uri: str,
        invitee_name: str,
        invitee_email: str,
        start_time: datetime,
        timezone: str = "America/Sao_Paulo",
        additional_info: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um evento/agendamento no Calendly
        
        Args:
            event_type_uri: URI do tipo de evento
            invitee_name: Nome do convidado
            invitee_email: Email do convidado
            start_time: Data/hora do evento
            timezone: Fuso horário
            additional_info: Informações adicionais
            
        Returns:
            Dados do evento criado
        """
        try:
            url = f"{self.base_url}/api/v1/scheduled_events"
            
            payload = {
                "event_type": event_type_uri,
                "invitees": [{
                    "name": invitee_name,
                    "email": invitee_email
                }],
                "start_time": start_time.isoformat(),
                "timezone": timezone
            }
            
            if additional_info:
                payload["invitees"][0]["questions_and_answers"] = [{
                    "question": "Informações adicionais",
                    "answer": additional_info
                }]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Erro ao criar evento: {e}")
            raise
    
    async def cancel_event(
        self,
        event_uri: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Cancela um evento agendado
        
        Args:
            event_uri: URI do evento
            reason: Motivo do cancelamento (opcional)
            
        Returns:
            True se cancelado com sucesso
        """
        try:
            url = f"{event_uri}/cancellation"
            
            payload = {}
            if reason:
                payload["reason"] = reason
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                return True
                
        except Exception as e:
            logger.error(f"Erro ao cancelar evento: {e}")
            return False
    
    async def get_event_types(self) -> List[Dict[str, Any]]:
        """
        Lista tipos de eventos disponíveis
        
        Returns:
            Lista de tipos de eventos
        """
        try:
            url = f"{self.base_url}/api/v1/event_types"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                return data.get("collection", [])
                
        except Exception as e:
            logger.error(f"Erro ao listar tipos de eventos: {e}")
            return []
    
    async def get_event(self, event_uri: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes de um evento específico
        
        Args:
            event_uri: URI do evento
            
        Returns:
            Dados do evento ou None se não encontrado
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    event_uri,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Erro ao obter evento: {e}")
            return None
    
    def parse_webhook(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Processa webhook do Calendly
        
        Args:
            webhook_data: Dados do webhook
            
        Returns:
            Evento formatado ou None
        """
        try:
            event_type = webhook_data.get("event")
            
            if event_type == "invitee.created":
                payload = webhook_data.get("payload", {})
                event = payload.get("event", {})
                invitee = payload.get("invitee", {})
                
                return {
                    "type": "event_created",
                    "event_uri": event.get("uri"),
                    "start_time": event.get("start_time"),
                    "invitee_name": invitee.get("name"),
                    "invitee_email": invitee.get("email"),
                    "cancel_url": invitee.get("cancel_url")
                }
            elif event_type == "invitee.canceled":
                payload = webhook_data.get("payload", {})
                event = payload.get("event", {})
                invitee = payload.get("invitee", {})
                
                return {
                    "type": "event_canceled",
                    "event_uri": event.get("uri"),
                    "invitee_email": invitee.get("email")
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao processar webhook Calendly: {e}")
            return None

