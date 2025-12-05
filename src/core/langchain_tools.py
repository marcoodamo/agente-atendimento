"""
LangChain Tools para os módulos do agente
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.config.config import config

logger = logging.getLogger(__name__)


class CalendlySearchInput(BaseModel):
    """Input para busca de horários no Calendly"""
    event_type_uri: str = Field(description="URI do tipo de evento no Calendly")
    start_date: Optional[str] = Field(default=None, description="Data inicial (ISO format)")
    end_date: Optional[str] = Field(default=None, description="Data final (ISO format)")


class CalendlyCreateEventInput(BaseModel):
    """Input para criar evento no Calendly"""
    event_type_uri: str = Field(description="URI do tipo de evento")
    invitee_name: str = Field(description="Nome do convidado")
    invitee_email: str = Field(description="Email do convidado")
    start_time: str = Field(description="Data/hora do evento (ISO format)")
    timezone: str = Field(default="America/Sao_Paulo", description="Fuso horário")
    additional_info: Optional[str] = Field(default=None, description="Informações adicionais")


class WhatsAppSendMessageInput(BaseModel):
    """Input para enviar mensagem WhatsApp"""
    phone_number: str = Field(description="Número do telefone (formato: 5511999999999)")
    message: str = Field(description="Texto da mensagem")


class KnowledgeSearchInput(BaseModel):
    """Input para busca na base de conhecimento"""
    query: str = Field(description="Pergunta ou termo de busca")
    top_k: int = Field(default=5, description="Número de resultados")


class CalendlySearchTool(BaseTool):
    """Tool para buscar horários disponíveis no Calendly"""
    name: str = "calendly_search_available_times"
    description: str = """
    Busca horários disponíveis para agendamento no Calendly.
    Use esta ferramenta quando o cliente perguntar sobre disponibilidade ou quiser agendar.
    Retorna uma lista de slots de horário disponíveis.
    Requer event_type_uri (URI do tipo de evento no Calendly).
    """
    args_schema: type = CalendlySearchInput
    
    def _run(self, event_type_uri: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """Executa busca de horários (síncrono)"""
        import asyncio
        try:
            return asyncio.run(self._arun(event_type_uri, start_date, end_date))
        except Exception as e:
            logger.error(f"Erro ao buscar horários: {e}")
            return f"Erro ao buscar horários disponíveis: {str(e)}"
    
    async def _arun(self, event_type_uri: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """Versão assíncrona"""
        try:
            from src.modules.calendly.calendly_service import CalendlyService
            
            calendly_service = CalendlyService()
            
            start_time = datetime.fromisoformat(start_date) if start_date else None
            end_time = datetime.fromisoformat(end_date) if end_date else None
            
            available_times = await calendly_service.get_available_times(
                event_type_uri=event_type_uri,
                start_time=start_time,
                end_time=end_time
            )
            
            if not available_times:
                return "Não há horários disponíveis no período solicitado."
            
            result = "Horários disponíveis:\n"
            for i, slot in enumerate(available_times[:10], 1):
                result += f"{i}. {slot.get('start_time', 'N/A')}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao buscar horários: {e}")
            return f"Erro ao buscar horários disponíveis: {str(e)}"


class CalendlyCreateEventTool(BaseTool):
    """Tool para criar evento no Calendly"""
    name: str = "calendly_create_event"
    description: str = """
    Cria um agendamento/evento no Calendly.
    Use esta ferramenta quando o cliente confirmar um horário para agendar.
    Requer: tipo de evento, nome, email, data/hora e fuso horário.
    """
    args_schema: type = CalendlyCreateEventInput
    
    async def _arun(
        self,
        event_type_uri: str,
        invitee_name: str,
        invitee_email: str,
        start_time: str,
        timezone: str = "America/Sao_Paulo",
        additional_info: Optional[str] = None
    ) -> str:
        """Cria evento no Calendly"""
        try:
            from src.modules.calendly.calendly_service import CalendlyService
            
            calendly_service = CalendlyService()
            event_datetime = datetime.fromisoformat(start_time)
            
            event = await calendly_service.create_event(
                event_type_uri=event_type_uri,
                invitee_name=invitee_name,
                invitee_email=invitee_email,
                start_time=event_datetime,
                timezone=timezone,
                additional_info=additional_info
            )
            
            return f"Agendamento criado com sucesso! Evento: {event.get('uri', 'N/A')}"
            
        except Exception as e:
            logger.error(f"Erro ao criar evento: {e}")
            return f"Erro ao criar agendamento: {str(e)}"
    
    def _run(self, *args, **kwargs) -> str:
        """Versão síncrona"""
        import asyncio
        try:
            return asyncio.run(self._arun(*args, **kwargs))
        except Exception as e:
            logger.error(f"Erro: {e}")
            return f"Erro: {str(e)}"


class WhatsAppSendMessageTool(BaseTool):
    """Tool para enviar mensagem via WhatsApp"""
    name: str = "whatsapp_send_message"
    description: str = """
    Envia mensagem de texto via WhatsApp.
    Use esta ferramenta quando precisar enviar uma mensagem ao cliente.
    Requer número de telefone e mensagem.
    """
    args_schema: type = WhatsAppSendMessageInput
    
    async def _arun(self, phone_number: str, message: str) -> str:
        """Envia mensagem WhatsApp"""
        try:
            from src.modules.whatsapp.whatsapp_service import WhatsAppService
            
            whatsapp_service = WhatsAppService()
            result = await whatsapp_service.send_text_message(
                phone_number=phone_number,
                message=message
            )
            
            return f"Mensagem enviada com sucesso. ID: {result.get('key', {}).get('id', 'N/A')}"
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            return f"Erro ao enviar mensagem: {str(e)}"
    
    def _run(self, *args, **kwargs) -> str:
        """Versão síncrona"""
        import asyncio
        try:
            return asyncio.run(self._arun(*args, **kwargs))
        except Exception as e:
            logger.error(f"Erro: {e}")
            return f"Erro: {str(e)}"


def get_available_tools() -> List[BaseTool]:
    """
    Retorna lista de tools disponíveis baseado nos módulos ativos
    """
    tools = []
    
    if config.agent.enable_agendamento:
        tools.append(CalendlySearchTool())
        tools.append(CalendlyCreateEventTool())
    
    # WhatsApp tool pode ser usado mesmo sem módulo ativo (para respostas)
    # Mas vamos incluir apenas se necessário
    
    return tools

