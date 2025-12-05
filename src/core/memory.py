"""
Gerenciamento de memória e contexto das conversas com Redis
Implementa memória com últimas 5 mensagens + sumário da conversa
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

from src.config.config import config
from src.utils.redis_client import redis_client
from src.core.langchain_agent import LangChainAgent

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Representa uma mensagem na conversa"""
    role: str  # "user" ou "assistant"
    content: str
    timestamp: datetime
    channel: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "channel": self.channel,
            "metadata": self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Cria Message a partir de dicionário"""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            channel=data["channel"],
            metadata=data.get("metadata")
        )


class ConversationMemory:
    """
    Gerencia a memória de conversas dos usuários usando Redis
    Mantém últimas 5 mensagens + sumário da conversa
    """
    
    def __init__(self):
        self.redis = redis_client
        self.recent_count = config.agent.recent_messages_count
        self.enable_summary = config.agent.enable_conversation_summary
        self.summary_threshold = config.agent.summary_update_threshold
        self._summary_agent: Optional[LangChainAgent] = None
    
    async def initialize(self):
        """Inicializa conexão Redis"""
        try:
            if not self.redis._client:
                await self.redis.connect()
        except Exception as e:
            logger.warning(f"Erro ao conectar ao Redis: {e}. Continuando sem Redis (modo fallback).")
            # Em modo fallback, usar dicionário em memória temporário
            if not hasattr(self, '_fallback_storage'):
                self._fallback_storage = {}
    
    def _get_conversation_key(self, user_id: str) -> str:
        """Chave Redis para histórico de mensagens"""
        return f"conversation:{user_id}:messages"
    
    def _get_summary_key(self, user_id: str) -> str:
        """Chave Redis para sumário da conversa"""
        return f"conversation:{user_id}:summary"
    
    def _get_profile_key(self, user_id: str) -> str:
        """Chave Redis para perfil do usuário"""
        return f"user:{user_id}:profile"
    
    def _get_message_count_key(self, user_id: str) -> str:
        """Chave Redis para contador de mensagens"""
        return f"conversation:{user_id}:count"
    
    async def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        channel: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Adiciona uma mensagem ao histórico do usuário
        Mantém apenas as últimas N mensagens + atualiza sumário quando necessário
        """
        await self.initialize()
        
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            channel=channel,
            metadata=metadata
        )
        
        # Adicionar mensagem à lista Redis (mantém apenas últimas N)
        key = self._get_conversation_key(user_id)
        message_data = json.dumps(message.to_dict())
        
        # Adicionar no início da lista
        await self.redis.client.lpush(key, message_data)
        
        # Manter apenas as últimas N mensagens
        await self.redis.client.ltrim(key, 0, self.recent_count - 1)
        
        # Definir TTL (expira após 90 dias de inatividade)
        await self.redis.client.expire(key, 90 * 24 * 60 * 60)
        
        # Incrementar contador de mensagens
        count_key = self._get_message_count_key(user_id)
        message_count = await self.redis.client.incr(count_key)
        await self.redis.client.expire(count_key, 90 * 24 * 60 * 60)
        
        # Atualizar sumário se necessário
        if self.enable_summary and message_count % self.summary_threshold == 0:
            await self._update_summary(user_id)
        
        logger.debug(f"Mensagem adicionada para {user_id}. Total: {message_count}")
    
    async def get_conversation_history(
        self,
        user_id: str,
        max_turns: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna o histórico de conversa do usuário
        Inclui últimas N mensagens + sumário da conversa
        
        Args:
            user_id: ID do usuário
            max_turns: Número máximo de turnos a retornar (padrão: recent_count)
            
        Returns:
            Lista de mensagens formatadas (mais recentes primeiro)
        """
        await self.initialize()
        
        max_turns = max_turns or self.recent_count
        
        # Verificar se Redis está disponível
        if self.redis._client:
            try:
                key = self._get_conversation_key(user_id)
                # Obter mensagens do Redis
                messages_data = await self.redis.client.lrange(key, 0, max_turns - 1)
                
                messages = []
                for msg_data in messages_data:
                    try:
                        msg_dict = json.loads(msg_data)
                        messages.append({
                            "role": msg_dict["role"],
                            "content": msg_dict["content"],
                            "timestamp": msg_dict["timestamp"],
                            "channel": msg_dict["channel"]
                        })
                    except Exception as e:
                        logger.error(f"Erro ao parsear mensagem: {e}")
                
                # Inverter para ordem cronológica (mais antigas primeiro)
                messages.reverse()
                return messages
            except Exception as e:
                logger.error(f"Erro ao buscar mensagens do Redis: {e}. Usando fallback.")
                return self._get_from_fallback(user_id, max_turns)
        else:
            # Modo fallback
            return self._get_from_fallback(user_id, max_turns)
    
    def _get_from_fallback(self, user_id: str, max_turns: int) -> List[Dict[str, Any]]:
        """Obtém mensagens do fallback"""
        if hasattr(self, '_fallback_storage') and user_id in self._fallback_storage:
            return self._fallback_storage[user_id][-max_turns:]
        return []
    
    async def get_conversation_context(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Retorna contexto completo da conversa:
        - Últimas N mensagens
        - Sumário da conversa (se disponível)
        
        Returns:
            Dict com messages e summary
        """
        messages = await self.get_conversation_history(user_id)
        summary = await self.get_summary(user_id)
        
        return {
            "messages": messages,
            "summary": summary,
            "message_count": len(messages)
        }
    
    async def get_summary(self, user_id: str) -> Optional[str]:
        """Retorna sumário da conversa"""
        await self.initialize()
        
        if self.redis._client:
            try:
                summary_key = self._get_summary_key(user_id)
                summary = await self.redis.client.get(summary_key)
                if summary:
                    return summary
            except Exception as e:
                logger.error(f"Erro ao buscar sumário do Redis: {e}")
        
        return None
    
    async def _update_summary(self, user_id: str):
        """
        Atualiza sumário da conversa usando LLM
        """
        try:
            await self.initialize()
            
            # Obter todas as mensagens recentes
            all_messages = await self.get_conversation_history(user_id, max_turns=50)
            
            if len(all_messages) < 5:
                # Muito poucas mensagens, não precisa de sumário
                return
            
            # Obter sumário anterior
            previous_summary = await self.get_summary(user_id)
            
            # Criar prompt para sumário
            summary_prompt = self._create_summary_prompt(all_messages, previous_summary)
            
            # Gerar sumário usando LLM
            if not self._summary_agent:
                from src.core.langchain_agent import LangChainAgent
                self._summary_agent = LangChainAgent()
            
            # Usar LLM diretamente para gerar sumário
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=config.llm.model,
                temperature=0.3,  # Temperatura baixa para sumários mais consistentes
                openai_api_key=config.llm.openai_api_key
            )
            
            response = await llm.ainvoke(summary_prompt)
            new_summary = response.content if hasattr(response, 'content') else str(response)
            
            # Salvar sumário no Redis
            summary_key = self._get_summary_key(user_id)
            await self.redis.client.set(summary_key, new_summary)
            await self.redis.client.expire(summary_key, 90 * 24 * 60 * 60)
            
            logger.info(f"Sumário atualizado para {user_id}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar sumário: {e}")
    
    def _create_summary_prompt(
        self,
        messages: List[Dict[str, Any]],
        previous_summary: Optional[str] = None
    ) -> str:
        """Cria prompt para gerar sumário da conversa"""
        prompt_parts = []
        
        prompt_parts.append("Você é um assistente que cria sumários concisos de conversas.")
        prompt_parts.append("\n## Instruções:")
        prompt_parts.append("- Crie um sumário objetivo e conciso da conversa")
        prompt_parts.append("- Destaque pontos principais, decisões tomadas e informações importantes")
        prompt_parts.append("- Mantenha o sumário em português brasileiro")
        prompt_parts.append("- Se houver sumário anterior, incorpore as novas informações")
        
        if previous_summary:
            prompt_parts.append(f"\n## Sumário Anterior:\n{previous_summary}")
            prompt_parts.append("\n## Novas Mensagens:")
        else:
            prompt_parts.append("\n## Conversa:")
        
        # Adicionar mensagens
        for msg in messages:
            role_name = "Cliente" if msg["role"] == "user" else "Assistente"
            prompt_parts.append(f"\n{role_name}: {msg['content']}")
        
        prompt_parts.append("\n\nCrie um sumário atualizado desta conversa:")
        
        return "\n".join(prompt_parts)
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Retorna o perfil do usuário"""
        await self.initialize()
        
        profile_key = self._get_profile_key(user_id)
        profile_data = await self.redis.hgetall(profile_key)
        
        return profile_data if profile_data else {}
    
    async def update_user_profile(
        self,
        user_id: str,
        data: Dict[str, Any]
    ):
        """Atualiza o perfil do usuário"""
        await self.initialize()
        
        profile_key = self._get_profile_key(user_id)
        
        for key, value in data.items():
            await self.redis.hset(profile_key, key, value)
        
        await self.redis.client.expire(profile_key, 90 * 24 * 60 * 60)
    
    async def clear_conversation(self, user_id: str):
        """Limpa o histórico de conversa de um usuário"""
        await self.initialize()
        
        keys_to_delete = [
            self._get_conversation_key(user_id),
            self._get_summary_key(user_id),
            self._get_message_count_key(user_id)
        ]
        
        for key in keys_to_delete:
            await self.redis.client.delete(key)
        
        logger.info(f"Conversa limpa para {user_id}")
    
    async def get_recent_conversations(
        self,
        hours: int = 24
    ) -> Dict[str, List[Message]]:
        """
        Retorna conversas recentes (últimas X horas)
        """
        await self.initialize()
        
        # Buscar todas as chaves de conversação
        pattern = "conversation:*:messages"
        keys = []
        async for key in self.redis.client.scan_iter(match=pattern):
            keys.append(key)
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = {}
        
        for key in keys:
            # Extrair user_id da chave
            user_id = key.split(":")[1]
            
            # Obter última mensagem
            last_msg_data = await self.redis.client.lindex(key, 0)
            if last_msg_data:
                try:
                    msg_dict = json.loads(last_msg_data)
                    msg_time = datetime.fromisoformat(msg_dict["timestamp"])
                    
                    if msg_time >= cutoff:
                        messages = await self.get_conversation_history(user_id)
                        if messages:
                            recent[user_id] = [
                                Message.from_dict(m) for m in messages
                            ]
                except Exception as e:
                    logger.error(f"Erro ao processar conversa {user_id}: {e}")
        
        return recent
