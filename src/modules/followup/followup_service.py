"""
Serviço de follow-up automático
Gerencia envio de mensagens de acompanhamento e reengajamento
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from src.config.config import config

logger = logging.getLogger(__name__)


class FollowUpType(Enum):
    """Tipos de follow-up"""
    POST_SERVICE = "post_service"  # Após atendimento
    POST_PURCHASE = "post_purchase"  # Após compra
    REMINDER = "reminder"  # Lembrete
    REENGAGEMENT = "reengagement"  # Reengajamento


@dataclass
class FollowUpTask:
    """Tarefa de follow-up agendada"""
    user_id: str
    channel: str
    followup_type: FollowUpType
    scheduled_time: datetime
    message_template: str
    metadata: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, sent, cancelled


class FollowUpService:
    """
    Serviço para gerenciar follow-ups automáticos
    """
    
    def __init__(self):
        # Em produção, isso seria um banco de dados ou fila (Redis/Celery)
        self._pending_followups: List[FollowUpTask] = []
        self._sent_followups: List[FollowUpTask] = []
    
    async def schedule_followup(
        self,
        user_id: str,
        channel: str,
        followup_type: FollowUpType,
        delay_hours: int,
        message_template: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FollowUpTask:
        """
        Agenda um follow-up
        
        Args:
            user_id: ID do usuário
            channel: Canal de comunicação (whatsapp, email, etc.)
            followup_type: Tipo de follow-up
            delay_hours: Horas até o envio
            message_template: Template da mensagem
            metadata: Metadados adicionais
            
        Returns:
            Tarefa de follow-up criada
        """
        scheduled_time = datetime.utcnow() + timedelta(hours=delay_hours)
        
        task = FollowUpTask(
            user_id=user_id,
            channel=channel,
            followup_type=followup_type,
            scheduled_time=scheduled_time,
            message_template=message_template,
            metadata=metadata
        )
        
        self._pending_followups.append(task)
        logger.info(f"Follow-up agendado para {user_id} em {scheduled_time}")
        
        return task
    
    async def schedule_post_service_followup(
        self,
        user_id: str,
        channel: str,
        delay_hours: int = 24
    ):
        """
        Agenda follow-up pós-atendimento padrão
        """
        message = (
            "Olá! Esperamos que tenha conseguido resolver sua questão. "
            "Há algo mais em que possamos ajudar?"
        )
        
        return await self.schedule_followup(
            user_id=user_id,
            channel=channel,
            followup_type=FollowUpType.POST_SERVICE,
            delay_hours=delay_hours,
            message_template=message
        )
    
    async def schedule_reminder(
        self,
        user_id: str,
        channel: str,
        reminder_time: datetime,
        message: str
    ):
        """
        Agenda um lembrete específico
        """
        delay_hours = (reminder_time - datetime.utcnow()).total_seconds() / 3600
        
        return await self.schedule_followup(
            user_id=user_id,
            channel=channel,
            followup_type=FollowUpType.REMINDER,
            delay_hours=int(delay_hours),
            message_template=message
        )
    
    async def process_pending_followups(self):
        """
        Processa follow-ups pendentes que estão prontos para envio
        Deve ser chamado periodicamente (ex: via Celery beat ou cron)
        """
        now = datetime.utcnow()
        ready_followups = [
            task for task in self._pending_followups
            if task.status == "pending" and task.scheduled_time <= now
        ]
        
        for task in ready_followups:
            try:
                await self._send_followup(task)
                task.status = "sent"
                self._sent_followups.append(task)
                self._pending_followups.remove(task)
            except Exception as e:
                logger.error(f"Erro ao enviar follow-up para {task.user_id}: {e}")
                task.status = "error"
    
    async def _send_followup(self, task: FollowUpTask):
        """
        Envia um follow-up específico
        """
        # Personalizar mensagem com dados do usuário se disponíveis
        message = task.message_template
        
        # Enviar via canal apropriado
        if task.channel == "whatsapp":
            from src.modules.whatsapp.whatsapp_service import WhatsAppService
            whatsapp_service = WhatsAppService()
            
            # Obter número do telefone do metadata ou user_id
            phone_number = task.metadata.get("phone_number") if task.metadata else task.user_id
            
            await whatsapp_service.send_text_message(
                phone_number=phone_number,
                message=message
            )
            
        elif task.channel == "email":
            # Implementar envio de email
            logger.info(f"Enviando email follow-up para {task.user_id}")
            # TODO: Implementar serviço de email
        
        logger.info(f"Follow-up enviado para {task.user_id} via {task.channel}")
    
    async def cancel_followup(self, user_id: str, followup_type: Optional[FollowUpType] = None):
        """
        Cancela follow-ups pendentes de um usuário
        """
        cancelled = []
        for task in self._pending_followups:
            if task.user_id == user_id:
                if followup_type is None or task.followup_type == followup_type:
                    task.status = "cancelled"
                    cancelled.append(task)
        
        for task in cancelled:
            self._pending_followups.remove(task)
        
        logger.info(f"Cancelled {len(cancelled)} follow-ups para {user_id}")
        return len(cancelled)
    
    def get_pending_followups(self, user_id: Optional[str] = None) -> List[FollowUpTask]:
        """
        Retorna follow-ups pendentes
        """
        if user_id:
            return [task for task in self._pending_followups if task.user_id == user_id]
        return self._pending_followups.copy()

