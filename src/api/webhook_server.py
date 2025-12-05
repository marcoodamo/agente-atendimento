"""
Servidor de webhooks e API REST
"""
import logging
import json
from fastapi import FastAPI, Request, HTTPException, Depends, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
import shutil
from pathlib import Path

from sqlalchemy import text

from src.config.config import config
from src.core.orchestrator import AgentOrchestrator
from src.modules.whatsapp.whatsapp_service import WhatsAppService
from src.modules.calendly.calendly_service import CalendlyService
from src.modules.followup.followup_service import FollowUpService
from src.api.auth import api_key_auth

logger = logging.getLogger(__name__)

# Inicializar serviços globalmente (lazy initialization)
_orchestrator: Optional[AgentOrchestrator] = None
_whatsapp_service: Optional[WhatsAppService] = None
_calendly_service: Optional[CalendlyService] = None
_followup_service: Optional[FollowUpService] = None


def get_orchestrator() -> AgentOrchestrator:
    """Obtém instância do orquestrador (lazy initialization)"""
    global _orchestrator
    if _orchestrator is None:
        try:
            _orchestrator = AgentOrchestrator()
        except Exception as e:
            logger.error(f"Erro ao inicializar orquestrador: {e}", exc_info=True)
            raise
    return _orchestrator


def get_whatsapp_service() -> WhatsAppService:
    """Obtém instância do serviço WhatsApp"""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service


def get_calendly_service() -> CalendlyService:
    """Obtém instância do serviço Calendly"""
    global _calendly_service
    if _calendly_service is None:
        _calendly_service = CalendlyService()
    return _calendly_service


def get_followup_service() -> FollowUpService:
    """Obtém instância do serviço Follow-up"""
    global _followup_service
    if _followup_service is None:
        _followup_service = FollowUpService()
    return _followup_service


class MessageRequest(BaseModel):
    """Request para processar mensagem"""
    message: str = Field(..., description="Mensagem do usuário", example="Olá, preciso de ajuda com meu pedido")
    user_id: str = Field(..., description="ID único do usuário", example="user123")
    channel: str = Field(..., description="Canal de comunicação", example="whatsapp")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Metadados opcionais (nome, telefone, etc.)",
        example={"name": "João Silva", "phone": "+5511999999999"}
    )
    rag_metadata_filter: Optional[Dict[str, Any]] = Field(
        None,
        description="Filtros de metadata para busca RAG (ex: {\"departamento\": \"TI\"})",
        example={"departamento": "TI", "categoria": "suporte"}
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Olá, preciso de ajuda com meu pedido",
                "user_id": "user123",
                "channel": "whatsapp",
                "metadata": {
                    "name": "João Silva",
                    "phone": "+5511999999999"
                }
            }
        }


class MessageResponse(BaseModel):
    """Resposta do agente"""
    response: str = Field(..., description="Resposta do agente")
    sources: List[str] = Field(default_factory=list, description="Fontes de informação utilizadas")
    timestamp: str = Field(..., description="Timestamp da resposta (ISO format)")
    agent_steps: List[Dict[str, Any]] = Field(default_factory=list, description="Passos do agente (se disponível)")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Olá! Como posso ajudá-lo hoje?",
                "sources": ["documento1.pdf", "politica_atendimento.pdf"],
                "timestamp": "2024-01-15T10:30:00.000Z",
                "agent_steps": []
            }
        }


class HealthResponse(BaseModel):
    """Resposta do health check"""
    status: str = Field(..., description="Status do serviço", example="healthy")


class ServiceInfoResponse(BaseModel):
    """Informações do serviço"""
    service: str = Field(..., description="Nome do serviço")
    status: str = Field(..., description="Status do serviço")
    version: str = Field(..., description="Versão da API")
    authentication: str = Field(..., description="Status da autenticação")


class WhatsAppWebhook(BaseModel):
    """Webhook do WhatsApp (Evolution API)"""
    event: str = Field(..., description="Tipo de evento")
    data: Dict[str, Any] = Field(..., description="Dados do evento")


class CalendlyWebhook(BaseModel):
    """Webhook do Calendly"""
    event: str = Field(..., description="Tipo de evento")
    payload: Dict[str, Any] = Field(..., description="Payload do evento")


class RAGSearchResponse(BaseModel):
    """Resposta da busca RAG"""
    results: List[Dict[str, Any]] = Field(..., description="Resultados da busca")


class RAGDocumentInfo(BaseModel):
    """Informações de um documento"""
    document_id: str = Field(..., description="ID único do documento")
    chunk_count: int = Field(..., description="Número de chunks do documento")
    created_at: Optional[str] = Field(None, description="Data de criação")
    updated_at: Optional[str] = Field(None, description="Data de atualização")
    source: Optional[str] = Field(None, description="Caminho do arquivo fonte")
    filename: Optional[str] = Field(None, description="Nome do arquivo original")


class RAGListDocumentsResponse(BaseModel):
    """Resposta de listagem de documentos"""
    documents: List[RAGDocumentInfo] = Field(..., description="Lista de documentos na base de conhecimento")
    total: int = Field(..., description="Total de documentos")


class RAGDeleteDocumentResponse(BaseModel):
    """Resposta de exclusão de documento"""
    status: str = Field(..., description="Status da operação")
    document_id: str = Field(..., description="ID do documento excluído")
    chunks_deleted: Optional[int] = Field(None, description="Número de chunks deletados")


class RAGAddDocumentRequest(BaseModel):
    """Request para adicionar documento"""
    file_path: str = Field(..., description="Caminho do arquivo a ser adicionado", example="/path/to/document.pdf")
    document_id: Optional[str] = Field(None, description="ID opcional do documento")
    selected_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata selecionada dos campos configurados", example={"departamento": "TI", "categoria": "Manual"})

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/path/to/document.pdf",
                "document_id": "doc_123",
                "selected_metadata": {"departamento": "TI", "categoria": "Manual"}
            }
        }


class MetadataFieldRequest(BaseModel):
    """Request para criar/editar campo de metadata"""
    field_key: str = Field(..., description="Chave única do campo", example="departamento")
    field_label: str = Field(..., description="Label amigável", example="Departamento")
    field_type: str = Field(default="text", description="Tipo do campo (text, number, select, date)", example="text")
    field_options: Optional[Dict[str, Any]] = Field(None, description="Opções adicionais (para select, validações)", example={"options": ["TI", "Vendas", "Suporte"]})


class MetadataFieldResponse(BaseModel):
    """Resposta de campo de metadata"""
    id: int
    field_key: str
    field_label: str
    field_type: str
    field_options: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MetadataFieldsListResponse(BaseModel):
    """Resposta de listagem de campos de metadata"""
    fields: List[MetadataFieldResponse]
    total: int


class UpdateMetadataRequest(BaseModel):
    """Request para atualizar metadata"""
    metadata_updates: Dict[str, Any] = Field(..., description="Campos de metadata a atualizar", example={"departamento": "TI", "categoria": "Manual"})


class ChunkInfoResponse(BaseModel):
    """Informações de um chunk"""
    chunk_index: int
    content: str
    content_full: str
    metadata: Dict[str, Any]
    source: Optional[str] = None
    created_at: Optional[str] = None


class DocumentChunksResponse(BaseModel):
    """Resposta de chunks de um documento"""
    document_id: str
    chunks: List[ChunkInfoResponse]
    total: int


class RAGAddDocumentResponse(BaseModel):
    """Resposta ao adicionar documento"""
    status: str = Field(..., description="Status da operação", example="success")
    document_id: str = Field(..., description="ID do documento adicionado")


def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI"""
    app = FastAPI(
        title=config.api.api_title,
        description="""
        API para atendimento automatizado via IA com LangChain e OpenAI.
        
        ## Funcionalidades
        
        - **Processamento de Mensagens**: Processa mensagens do usuário e retorna respostas inteligentes
        - **RAG (Base de Conhecimento)**: Busca e adiciona documentos à base de conhecimento
        - **Webhooks**: Recebe eventos do WhatsApp e Calendly
        
        ## Autenticação
        
        A maioria dos endpoints requer autenticação via API Key no header `X-API-Key`.
        Configure a variável `API_KEY` no arquivo `.env`.
        """,
        version=config.api.api_version,
        docs_url="/docs" if config.agent.environment == "development" else None,
        redoc_url="/redoc" if config.agent.environment == "development" else None,
        tags_metadata=[
            {
                "name": "Geral",
                "description": "Endpoints gerais do serviço"
            },
            {
                "name": "Mensagens",
                "description": "Processamento de mensagens do usuário"
            },
            {
                "name": "RAG",
                "description": "Gerenciamento da base de conhecimento (RAG)"
            },
            {
                "name": "Webhooks",
                "description": "Webhooks para integração com serviços externos"
            }
        ]
    )
    
    @app.get(
        "/",
        response_model=ServiceInfoResponse,
        tags=["Geral"],
        summary="Informações do serviço",
        description="Retorna informações sobre o serviço e status da autenticação"
    )
    async def root():
        """Endpoint raiz - Informações do serviço"""
        return ServiceInfoResponse(
            service=config.api.api_title,
            status="running",
            version=config.api.api_version,
            authentication="API Key required" if config.api.enable_auth else "disabled"
        )
    
    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["Geral"],
        summary="Health check",
        description="Verifica se o serviço está funcionando (não requer autenticação)"
    )
    async def health():
        """Health check (sem autenticação)"""
        return HealthResponse(status="healthy")
    
    @app.post(
        "/api/message",
        response_model=MessageResponse,
        tags=["Mensagens"],
        summary="Processar mensagem",
        description="""
        Processa uma mensagem do usuário e retorna a resposta do agente IA.
        
        O agente utiliza:
        - Histórico de conversas do usuário
        - Base de conhecimento RAG (se ativada)
        - Ferramentas disponíveis (Calendly, WhatsApp, etc.)
        
        **Requer autenticação via API Key no header `X-API-Key`**
        """
    )
    async def process_message(
        request: MessageRequest,
        api_key: str = Depends(api_key_auth.verify_api_key)
    ):
        """
        Endpoint para processar mensagem do usuário
        
        Requer autenticação via API Key no header X-API-Key
        
        Body:
        - message: Mensagem do usuário
        - user_id: ID único do usuário
        - channel: Canal de comunicação (whatsapp, webchat, api, etc.)
        - metadata: Metadados opcionais (nome, telefone, etc.)
        """
        try:
            orchestrator = get_orchestrator()
            result = await orchestrator.process_message(
                user_message=request.message,
                user_id=request.user_id,
                channel=request.channel,
                metadata=request.metadata,
                rag_metadata_filter=request.rag_metadata_filter
            )
            
            return MessageResponse(**result)
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post(
        "/webhook/whatsapp",
        tags=["Webhooks"],
        summary="Webhook WhatsApp",
        description="""
        Webhook para receber mensagens do WhatsApp via Evolution API.
        
        Quando uma mensagem é recebida:
        1. O agente processa a mensagem
        2. Uma resposta é gerada automaticamente
        3. A resposta é enviada via WhatsApp
        4. Um follow-up pode ser agendado (se o módulo estiver ativo)
        
        **Não requer autenticação** (configure validação de webhook na Evolution API)
        """
    )
    async def whatsapp_webhook(webhook_data: dict):
        """
        Webhook para receber mensagens do WhatsApp (Evolution API)
        """
        try:
            whatsapp_service = get_whatsapp_service()
            # Processar webhook
            message_data = whatsapp_service.parse_webhook_message(webhook_data)
            
            if not message_data:
                return {"status": "ignored"}
            
            # Extrair informações
            phone_number = message_data["phone_number"]
            content = message_data["content"]
            message_id = message_data["message_id"]
            
            # Processar mensagem com o agente
            orchestrator = get_orchestrator()
            result = await orchestrator.process_message(
                user_message=content,
                user_id=phone_number,
                channel="whatsapp",
                metadata={
                    "phone_number": phone_number,
                    "message_id": message_id,
                    "message_type": message_data["type"]
                }
            )
            
            # Enviar resposta via WhatsApp
            response_text = result["response"]
            await whatsapp_service.send_text_message(
                phone_number=phone_number,
                message=response_text
            )
            
            # Marcar mensagem como lida
            await whatsapp_service.mark_message_as_read(
                message_id=message_id,
                phone_number=phone_number
            )
            
            # Agendar follow-up se necessário
            if orchestrator.active_modules.get("followup"):
                followup_service = get_followup_service()
                await followup_service.schedule_post_service_followup(
                    user_id=phone_number,
                    channel="whatsapp"
                )
            
            return {"status": "processed", "response": response_text}
            
        except Exception as e:
            logger.error(f"Erro ao processar webhook WhatsApp: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    @app.post(
        "/webhook/calendly",
        tags=["Webhooks"],
        summary="Webhook Calendly",
        description="""
        Webhook para receber eventos do Calendly.
        
        Eventos suportados:
        - `event_created`: Quando um agendamento é criado
        - `event_canceled`: Quando um agendamento é cancelado
        
        **Configure o webhook secret no Calendly para validação**
        """
    )
    async def calendly_webhook(webhook_data: dict):
        """
        Webhook para receber eventos do Calendly
        """
        try:
            calendly_service = get_calendly_service()
            event_data = calendly_service.parse_webhook(webhook_data)
            
            if not event_data:
                return {"status": "ignored"}
            
            event_type = event_data["type"]
            
            if event_type == "event_created":
                # Notificar usuário sobre agendamento confirmado
                logger.info(f"Evento criado: {event_data}")
                # Aqui poderia enviar confirmação via WhatsApp ou email
                
            elif event_type == "event_canceled":
                # Notificar sobre cancelamento
                logger.info(f"Evento cancelado: {event_data}")
            
            return {"status": "processed"}
            
        except Exception as e:
            logger.error(f"Erro ao processar webhook Calendly: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    @app.post(
        "/api/rag/upload",
        response_model=RAGAddDocumentResponse,
        tags=["RAG"],
        summary="Upload de documento",
        description="""
        Faz upload de um arquivo e adiciona à base de conhecimento RAG.
        
        O arquivo será:
        1. Salvo no diretório de uploads
        2. Processado e dividido em chunks
        3. Convertido em embeddings
        4. Armazenado no PostgreSQL com PGVector usando índice HNSW
        
        Formatos suportados: PDF, DOCX, TXT
        
        **Requer autenticação via API Key**
        """
    )
    async def upload_document(
        file: UploadFile = File(..., description="Arquivo a ser enviado"),
        document_id: Optional[str] = Form(None, description="ID opcional do documento"),
        selected_metadata: Optional[str] = Form(None, description="Metadata selecionada em JSON (ex: {\"departamento\": \"TI\"})"),
        api_key: str = Depends(api_key_auth.verify_api_key)
    ):
        """
        Faz upload de arquivo e adiciona à base de conhecimento RAG
        """
        try:
            # Validar extensão
            allowed_extensions = {'.pdf', '.docx', '.doc', '.txt'}
            file_ext = Path(file.filename).suffix.lower()
            
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Formato não suportado. Use: {', '.join(allowed_extensions)}"
                )
            
            # Criar diretório de uploads se não existir
            uploads_dir = config.agent.uploads_dir
            uploads_dir.mkdir(parents=True, exist_ok=True)
            
            # Salvar arquivo
            file_path = uploads_dir / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            logger.info(f"Arquivo salvo em: {file_path}")
            
            # Verificar se módulo RAG está habilitado
            if not config.agent.enable_knowledge:
                raise HTTPException(
                    status_code=503,
                    detail="Módulo RAG está desabilitado. Habilite com ENABLE_KNOWLEDGE=true ou --knowledge"
                )
            
            # Processar e adicionar à base de conhecimento
            try:
                from src.modules.rag.rag_service import RAGService
                rag_service = RAGService()
                
                # Parse selected_metadata se fornecido
                selected_metadata_dict = None
                if selected_metadata and selected_metadata.strip():
                    try:
                        selected_metadata_dict = json.loads(selected_metadata)
                        # Validar que é um dicionário
                        if not isinstance(selected_metadata_dict, dict):
                            raise HTTPException(
                                status_code=400,
                                detail="selected_metadata deve ser um objeto JSON válido"
                            )
                    except json.JSONDecodeError as e:
                        logger.error(f"Erro ao fazer parse de selected_metadata: {e}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"selected_metadata deve ser um JSON válido: {str(e)}"
                        )
                
                logger.info(f"Adicionando documento: {file.filename}, metadata: {selected_metadata_dict}")
                
                doc_id = await rag_service.add_document(
                    file_path=str(file_path),
                    document_id=document_id,
                    metadata={"original_filename": file.filename, "uploaded_at": datetime.utcnow().isoformat()},
                    selected_metadata=selected_metadata_dict
                )
                
                return RAGAddDocumentResponse(status="success", document_id=doc_id)
            except HTTPException:
                # Re-raise HTTPException para manter status code correto
                raise
            except Exception as rag_error:
                logger.error(f"Erro ao processar documento RAG: {rag_error}", exc_info=True)
                # Se for erro de banco/extensão, dar mensagem mais clara
                error_str = str(rag_error).lower()
                if "vector" in error_str or "extension" in error_str or "pgvector" in error_str:
                    raise HTTPException(
                        status_code=503,
                        detail="Erro ao acessar banco de dados. Verifique se PostgreSQL com pgvector está rodando (docker-compose up -d)"
                    )
                if "connection" in error_str or "could not connect" in error_str:
                    raise HTTPException(
                        status_code=503,
                        detail="Erro de conexão com banco de dados. Verifique se o PostgreSQL está rodando."
                    )
                raise HTTPException(status_code=500, detail=f"Erro ao processar documento: {str(rag_error)}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao fazer upload de documento: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post(
        "/api/rag/add-document",
        response_model=RAGAddDocumentResponse,
        tags=["RAG"],
        summary="Adicionar documento (por caminho)",
        description="""
        Adiciona um documento à base de conhecimento RAG usando caminho do arquivo.
        
        Use este endpoint quando o arquivo já está no servidor.
        Para upload de arquivos, use `/api/rag/upload`.
        
        O documento será:
        1. Processado e dividido em chunks
        2. Convertido em embeddings
        3. Armazenado no PostgreSQL com PGVector usando índice HNSW
        
        Formatos suportados: PDF, DOCX, TXT
        
        **Requer autenticação via API Key**
        """
    )
    async def add_document(
        request: RAGAddDocumentRequest,
        api_key: str = Depends(api_key_auth.verify_api_key)
    ):
        """
        Adiciona documento à base de conhecimento RAG por caminho
        
        Requer autenticação via API Key
        
        Requer autenticação via API Key
        """
        try:
            from src.modules.rag.rag_service import RAGService
            rag_service = RAGService()
            
            doc_id = await rag_service.add_document(request.file_path, request.document_id)
            
            return RAGAddDocumentResponse(status="success", document_id=doc_id)
            
        except Exception as e:
            logger.error(f"Erro ao adicionar documento: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get(
        "/api/rag/search",
        response_model=RAGSearchResponse,
        tags=["RAG"],
        summary="Buscar na base de conhecimento",
        description="""
        Busca documentos relevantes na base de conhecimento usando busca vetorial.
        
        A busca utiliza embeddings para encontrar documentos similares à query.
        É possível filtrar por metadata usando o parâmetro metadata_filter como JSON.
        
        Exemplo de metadata_filter: {"departamento": "TI", "categoria": "suporte"}
        
        **Requer autenticação via API Key**
        """
    )
    async def search_knowledge(
        query: str = Query(..., description="Query de busca", example="Como funciona o processo de devolução?"),
        top_k: int = Query(5, description="Número de resultados a retornar", ge=1, le=20),
        similarity_threshold: float = Query(0.3, ge=0.0, le=1.0, description="Limite mínimo de similaridade (0.0 a 1.0)"),
        metadata_filter: Optional[str] = Query(None, description="Filtros de metadata em JSON (ex: {\"departamento\": \"TI\"})"),
        api_key: str = Depends(api_key_auth.verify_api_key)
    ):
        """
        Busca na base de conhecimento
        
        Requer autenticação via API Key
        """
        try:
            from src.modules.rag.rag_service import RAGService
            rag_service = RAGService()
            
            # Parse metadata_filter se fornecido
            metadata_dict = None
            if metadata_filter:
                try:
                    metadata_dict = json.loads(metadata_filter)
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=400,
                        detail="metadata_filter deve ser um JSON válido"
                    )
            
            results = await rag_service.search(
                query, 
                top_k=top_k, 
                similarity_threshold=similarity_threshold,
                metadata_filter=metadata_dict
            )
            
            return RAGSearchResponse(results=results)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get(
        "/api/rag/documents",
        response_model=RAGListDocumentsResponse,
        tags=["RAG"],
        summary="Listar documentos",
        description="""
        Lista todos os documentos na base de conhecimento RAG.
        
        Retorna informações agregadas de cada documento, incluindo:
        - ID do documento
        - Número de chunks
        - Data de criação e atualização
        - Nome do arquivo original
        
        **Requer autenticação via API Key**
        """
    )
    async def list_documents(
        api_key: str = Depends(api_key_auth.verify_api_key)
    ):
        """
        Lista todos os documentos na base de conhecimento
        """
        try:
            if not config.agent.enable_knowledge:
                raise HTTPException(
                    status_code=503,
                    detail="Módulo RAG está desabilitado. Habilite com ENABLE_KNOWLEDGE=true"
                )
            
            from src.modules.rag.rag_service import RAGService
            rag_service = RAGService()
            
            documents = await rag_service.list_documents()
            
            return RAGListDocumentsResponse(
                documents=documents,
                total=len(documents)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao listar documentos: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete(
        "/api/rag/documents/{document_id}",
        response_model=RAGDeleteDocumentResponse,
        tags=["RAG"],
        summary="Excluir documento",
        description="""
        Exclui um documento da base de conhecimento RAG.
        
        Remove todos os chunks associados ao documento.
        
        **Requer autenticação via API Key**
        """
    )
    async def delete_document(
        document_id: str,
        api_key: str = Depends(api_key_auth.verify_api_key)
    ):
        """
        Exclui um documento da base de conhecimento
        """
        try:
            if not config.agent.enable_knowledge:
                raise HTTPException(
                    status_code=503,
                    detail="Módulo RAG está desabilitado. Habilite com ENABLE_KNOWLEDGE=true"
                )
            
            from src.modules.rag.rag_service import RAGService
            rag_service = RAGService()
            
            # Obter número de chunks antes de deletar
            session = rag_service.SessionLocal()
            try:
                count_sql = text("SELECT COUNT(*) FROM document_chunks WHERE document_id = :doc_id")
                chunk_count = session.execute(count_sql, {"doc_id": document_id}).scalar()
            finally:
                session.close()
            
            success = await rag_service.delete_document(document_id)
            
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Documento {document_id} não encontrado"
                )
            
            return RAGDeleteDocumentResponse(
                status="success",
                document_id=document_id,
                chunks_deleted=chunk_count
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao excluir documento: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get(
        "/api/rag/metadata/fields",
        response_model=MetadataFieldsListResponse,
        tags=["RAG"],
        summary="Listar campos de metadata",
        description="""
        Lista todos os campos de metadata disponíveis/configurados.
        
        **Requer autenticação via API Key**
        """
    )
    async def list_metadata_fields(
        api_key: str = Depends(api_key_auth.verify_api_key)
    ):
        """Lista campos de metadata disponíveis"""
        try:
            if not config.agent.enable_knowledge:
                raise HTTPException(
                    status_code=503,
                    detail="Módulo RAG está desabilitado. Habilite com ENABLE_KNOWLEDGE=true"
                )
            
            from src.modules.rag.rag_service import RAGService
            rag_service = RAGService()
            
            fields = await rag_service.list_metadata_fields()
            
            return MetadataFieldsListResponse(
                fields=[MetadataFieldResponse(**field) for field in fields],
                total=len(fields)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao listar campos de metadata: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post(
        "/api/rag/metadata/fields",
        response_model=MetadataFieldResponse,
        tags=["RAG"],
        summary="Criar campo de metadata",
        description="""
        Cria um novo campo de metadata disponível.
        
        Quando um novo campo é criado, todos os documentos existentes terão esse campo setado como null.
        
        **Requer autenticação via API Key**
        """
    )
    async def create_metadata_field(
        request: MetadataFieldRequest,
        api_key: str = Depends(api_key_auth.verify_api_key)
    ):
        """Cria um novo campo de metadata"""
        try:
            if not config.agent.enable_knowledge:
                raise HTTPException(
                    status_code=503,
                    detail="Módulo RAG está desabilitado. Habilite com ENABLE_KNOWLEDGE=true"
                )
            
            from src.modules.rag.rag_service import RAGService
            rag_service = RAGService()
            
            field = await rag_service.create_metadata_field(
                field_key=request.field_key,
                field_label=request.field_label,
                field_type=request.field_type,
                field_options=request.field_options
            )
            
            return MetadataFieldResponse(**field)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao criar campo de metadata: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete(
        "/api/rag/metadata/fields/{field_key}",
        tags=["RAG"],
        summary="Remover campo de metadata",
        description="""
        Remove um campo de metadata.
        
        Remove o campo de todos os documentos existentes.
        
        **Requer autenticação via API Key**
        """
    )
    async def delete_metadata_field(
        field_key: str,
        api_key: str = Depends(api_key_auth.verify_api_key)
    ):
        """Remove um campo de metadata"""
        try:
            if not config.agent.enable_knowledge:
                raise HTTPException(
                    status_code=503,
                    detail="Módulo RAG está desabilitado. Habilite com ENABLE_KNOWLEDGE=true"
                )
            
            from src.modules.rag.rag_service import RAGService
            rag_service = RAGService()
            
            success = await rag_service.delete_metadata_field(field_key)
            
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Campo de metadata '{field_key}' não encontrado"
                )
            
            return {"status": "success", "field_key": field_key}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao remover campo de metadata: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.put(
        "/api/rag/documents/{document_id}/metadata",
        tags=["RAG"],
        summary="Atualizar metadata de documento",
        description="""
        Atualiza metadata de todos os chunks de um documento.
        
        **Requer autenticação via API Key**
        """
    )
    async def update_document_metadata(
        document_id: str,
        request: UpdateMetadataRequest,
        api_key: str = Depends(api_key_auth.verify_api_key)
    ):
        """Atualiza metadata de todos os chunks de um documento"""
        try:
            if not config.agent.enable_knowledge:
                raise HTTPException(
                    status_code=503,
                    detail="Módulo RAG está desabilitado. Habilite com ENABLE_KNOWLEDGE=true"
                )
            
            from src.modules.rag.rag_service import RAGService
            rag_service = RAGService()
            
            success = await rag_service.update_document_metadata(
                document_id=document_id,
                metadata_updates=request.metadata_updates
            )
            
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Documento {document_id} não encontrado"
                )
            
            return {"status": "success", "document_id": document_id}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar metadata do documento: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.put(
        "/api/rag/documents/{document_id}/chunks/{chunk_index}/metadata",
        tags=["RAG"],
        summary="Atualizar metadata de chunk",
        description="""
        Atualiza metadata de um chunk específico.
        
        **Requer autenticação via API Key**
        """
    )
    async def update_chunk_metadata(
        document_id: str,
        chunk_index: int,
        request: UpdateMetadataRequest,
        api_key: str = Depends(api_key_auth.verify_api_key)
    ):
        """Atualiza metadata de um chunk específico"""
        try:
            if not config.agent.enable_knowledge:
                raise HTTPException(
                    status_code=503,
                    detail="Módulo RAG está desabilitado. Habilite com ENABLE_KNOWLEDGE=true"
                )
            
            from src.modules.rag.rag_service import RAGService
            rag_service = RAGService()
            
            success = await rag_service.update_chunk_metadata(
                document_id=document_id,
                chunk_index=chunk_index,
                metadata_updates=request.metadata_updates
            )
            
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Chunk {document_id}:{chunk_index} não encontrado"
                )
            
            return {"status": "success", "document_id": document_id, "chunk_index": chunk_index}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar metadata do chunk: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get(
        "/api/rag/documents/{document_id}/chunks",
        response_model=DocumentChunksResponse,
        tags=["RAG"],
        summary="Listar chunks de documento",
        description="""
        Lista todos os chunks de um documento com suas metadata.
        
        **Requer autenticação via API Key**
        """
    )
    async def get_document_chunks(
        document_id: str,
        api_key: str = Depends(api_key_auth.verify_api_key)
    ):
        """Lista todos os chunks de um documento"""
        try:
            if not config.agent.enable_knowledge:
                raise HTTPException(
                    status_code=503,
                    detail="Módulo RAG está desabilitado. Habilite com ENABLE_KNOWLEDGE=true"
                )
            
            from src.modules.rag.rag_service import RAGService
            rag_service = RAGService()
            
            chunks = await rag_service.get_document_chunks(document_id)
            
            return DocumentChunksResponse(
                document_id=document_id,
                chunks=[ChunkInfoResponse(**chunk) for chunk in chunks],
                total=len(chunks)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao listar chunks do documento: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get(
        "/api/rag/documents/{document_id}/chunks/{chunk_index}/metadata",
        response_model=Dict[str, Any],
        tags=["RAG"],
        summary="Obter metadata de chunk",
        description="""
        Obtém metadata de um chunk específico.
        
        **Requer autenticação via API Key**
        """
    )
    async def get_chunk_metadata(
        document_id: str,
        chunk_index: int,
        api_key: str = Depends(api_key_auth.verify_api_key)
    ):
        """Obtém metadata de um chunk específico"""
        try:
            if not config.agent.enable_knowledge:
                raise HTTPException(
                    status_code=503,
                    detail="Módulo RAG está desabilitado. Habilite com ENABLE_KNOWLEDGE=true"
                )
            
            from src.modules.rag.rag_service import RAGService
            rag_service = RAGService()
            
            metadata = await rag_service.get_chunk_metadata(document_id, chunk_index)
            
            if metadata is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Chunk {document_id}:{chunk_index} não encontrado"
                )
            
            return metadata
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao obter metadata do chunk: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    return app

