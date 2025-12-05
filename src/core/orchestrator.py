"""
Orquestrador principal do agente IA
Gerencia o fluxo de conversação e coordena os módulos
Usa LangChain para processamento de mensagens
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.config.config import config
from src.core.memory import ConversationMemory
from src.core.langchain_agent import LangChainAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orquestrador que coordena todos os módulos do agente
    Usa LangChain Agent para processamento inteligente
    """
    
    def __init__(self):
        self.memory = ConversationMemory()
        self.langchain_agent = LangChainAgent()
        self.active_modules: Dict[str, bool] = {
            "agendamento": config.agent.enable_agendamento,
            "followup": config.agent.enable_followup,
            "voz": config.agent.enable_voz,
            "knowledge": config.agent.enable_knowledge,
            "transbordo_humano": config.agent.enable_transbordo_humano,
        }
    
    async def process_message(
        self,
        user_message: str,
        user_id: str,
        channel: str,
        metadata: Optional[Dict[str, Any]] = None,
        rag_metadata_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processa uma mensagem do usuário e retorna a resposta do agente
        Usa LangChain Agent para processamento inteligente
        
        Args:
            user_message: Mensagem do usuário
            user_id: Identificador único do usuário
            channel: Canal de comunicação (whatsapp, voice, webchat, etc.)
            metadata: Metadados adicionais (ex: número de telefone, nome, etc.)
            rag_metadata_filter: Filtros de metadata para busca RAG (ex: {"departamento": "TI"})
            
        Returns:
            Dict com a resposta do agente e metadados
        """
        try:
            # Recuperar contexto completo da conversa (últimas 5 mensagens + sumário)
            try:
                conversation_context = await self.memory.get_conversation_context(user_id)
                conversation_history = conversation_context.get("messages", [])
                conversation_summary = conversation_context.get("summary")
            except Exception as mem_error:
                logger.warning(f"Erro ao recuperar contexto do Redis: {mem_error}. Continuando sem histórico.")
                conversation_history = []
                conversation_summary = None
            
            # Buscar informações relevantes se módulo RAG estiver ativo
            context_documents = []
            if self.active_modules.get("knowledge"):
                from src.modules.rag.rag_service import RAGService
                rag_service = RAGService()
                # Usar threshold mais baixo (0.1) para melhor recall quando usado pelo agente
                # Isso permite encontrar mais documentos relevantes mesmo com similaridade menor
                context_documents = await rag_service.search(
                    query=user_message,
                    top_k=config.rag.top_k,
                    similarity_threshold=0.1,  # Threshold mais baixo para melhor recall
                    metadata_filter=rag_metadata_filter
                )
                logger.info(f"RAG encontrou {len(context_documents)} documentos relevantes para: {user_message}")
            
            # Processar mensagem usando LangChain Agent
            result = await self.langchain_agent.process_message(
                user_message=user_message,
                conversation_history=conversation_history,
                conversation_summary=conversation_summary,
                context_documents=context_documents,
                metadata=metadata
            )
            
            response = result.get("response", "")
            
            # Salvar na memória (Redis) - continuar mesmo se falhar
            try:
                await self.memory.add_message(
                    user_id=user_id,
                    role="user",
                    content=user_message,
                    channel=channel,
                    metadata=metadata
                )
            except Exception as mem_error:
                logger.warning(f"Erro ao salvar mensagem do usuário no Redis: {mem_error}. Continuando sem memória.")
            
            try:
                await self.memory.add_message(
                    user_id=user_id,
                    role="assistant",
                    content=response,
                    channel=channel
                )
            except Exception as mem_error:
                logger.warning(f"Erro ao salvar resposta do assistente no Redis: {mem_error}. Continuando sem memória.")
            
            return {
                "response": response,
                "sources": result.get("sources", []),
                "timestamp": result.get("timestamp", datetime.utcnow().isoformat()),
                "agent_steps": result.get("agent_steps", [])
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}", exc_info=True)
            return {
                "response": "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    

