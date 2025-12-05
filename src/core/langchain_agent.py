"""
Agente LangChain para o sistema
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.config.config import config
from src.core.langchain_tools import get_available_tools
from src.core.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class LangChainAgent:
    """
    Agente LangChain que coordena o processamento de mensagens
    """
    
    def __init__(self):
        self.llm = self._initialize_llm()
        self.prompt_manager = PromptManager()
        self.tools = get_available_tools()
        self.agent = self._create_agent()
    
    def _initialize_llm(self) -> ChatOpenAI:
        """Inicializa o LLM usando LangChain"""
        if not config.llm.openai_api_key:
            raise ValueError("OPENAI_API_KEY não configurada")
        
        return ChatOpenAI(
            model=config.llm.model,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
            openai_api_key=config.llm.openai_api_key,
            streaming=False
        )
    
    def _create_agent(self):
        """Cria o agente LangChain usando a nova API"""
        # Prompt do sistema
        system_prompt = self.prompt_manager.get_system_prompt()
        
        try:
            # Criar agente usando a nova API do LangChain 1.1.0
            agent = create_agent(
                model=self.llm,
                tools=self.tools if self.tools else None,
                system_prompt=system_prompt,
                debug=False
            )
            return agent
        except Exception as e:
            logger.warning(f"Erro ao criar agente com create_agent: {e}. Usando LLM direto.")
            # Fallback: retornar None e usar LLM diretamente
            return None
    
    async def process_message(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        conversation_summary: Optional[str] = None,
        context_documents: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processa mensagem usando LangChain Agent
        
        Args:
            user_message: Mensagem do usuário
            conversation_history: Histórico de conversa (últimas 5 mensagens)
            conversation_summary: Sumário da conversa anterior
            context_documents: Documentos de contexto (RAG)
            metadata: Metadados adicionais
            
        Returns:
            Resposta do agente e metadados
        """
        try:
            # Construir histórico de mensagens para LangChain (apenas últimas 5)
            chat_history = []
            
            if conversation_history:
                # Usar apenas as últimas mensagens (já vem limitado da memória)
                for msg in conversation_history[-5:]:
                    if msg["role"] == "user":
                        chat_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        chat_history.append(AIMessage(content=msg["content"]))
            
            # Construir input com contexto completo
            context_parts = []
            
            # Adicionar sumário da conversa se disponível
            if conversation_summary:
                context_parts.append(f"## Resumo da Conversa Anterior:\n{conversation_summary}\n")
            
            # Adicionar contexto de documentos RAG se disponível
            if context_documents:
                context_parts.append("## Informações Relevantes da Base de Conhecimento:")
                for i, doc in enumerate(context_documents, 1):
                    context_parts.append(f"\n[{i}] {doc.get('content', '')}")
                    if doc.get('source'):
                        context_parts.append(f"Fonte: {doc['source']}")
            
            # Adicionar informações do usuário se disponíveis
            if metadata:
                if metadata.get("name"):
                    context_parts.insert(0, f"[Cliente: {metadata['name']}]")
            
            # Montar input final
            if context_parts:
                input_with_context = "\n".join(context_parts) + "\n\n## Mensagem Atual do Cliente:\n" + user_message
            else:
                input_with_context = user_message
            
            # Construir mensagens para o agente
            messages = []
            
            # Adicionar histórico
            messages.extend(chat_history)
            
            # Adicionar mensagem atual com contexto
            messages.append(HumanMessage(content=input_with_context))
            
            # Executar agente ou LLM diretamente
            try:
                if self.agent is not None:
                    # Usar agente se disponível
                    result = await self.agent.ainvoke({
                        "messages": messages
                    })
                    
                    # Extrair resposta das mensagens retornadas
                    if isinstance(result, dict):
                        if "messages" in result:
                            # Pegar última mensagem do assistente
                            last_message = result["messages"][-1]
                            response = last_message.content if hasattr(last_message, 'content') else str(last_message)
                        elif "output" in result:
                            response = result["output"]
                        else:
                            response = str(result)
                    else:
                        response = str(result)
                else:
                    # Fallback: usar LLM diretamente com tools
                    if self.tools:
                        # Bind tools ao LLM
                        llm_with_tools = self.llm.bind_tools(self.tools)
                        response_obj = await llm_with_tools.ainvoke(messages)
                    else:
                        response_obj = await self.llm.ainvoke(messages)
                    
                    response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
                
            except Exception as e:
                logger.error(f"Erro ao executar agente: {e}", exc_info=True)
                # Fallback final: usar LLM diretamente sem tools
                try:
                    response_obj = await self.llm.ainvoke(messages)
                    response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
                except Exception as e2:
                    logger.error(f"Erro ao usar LLM diretamente: {e2}")
                    response = "Desculpe, ocorreu um erro ao processar sua mensagem."
            
            return {
                "response": response,
                "sources": [doc.get("source") for doc in context_documents] if context_documents else [],
                "timestamp": datetime.utcnow().isoformat(),
                "agent_steps": []  # Nova API não retorna intermediate_steps da mesma forma
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem com LangChain: {e}", exc_info=True)
            return {
                "response": "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

