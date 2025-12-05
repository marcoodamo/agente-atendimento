"""
Serviço RAG - Busca e recuperação de informações da base de conhecimento
"""
import logging
from typing import List, Dict, Optional, Any
import asyncio
import json
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import numpy as np

from src.config.config import config
from src.modules.rag.embedding_service import EmbeddingService
from src.modules.rag.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class RAGService:
    """
    Serviço de Retrieval-Augmented Generation
    Gerencia busca vetorial e recuperação de documentos
    """
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.document_processor = DocumentProcessor()
        self._initialize_database()
    
    def _initialize_database(self):
        """Inicializa conexão com PostgreSQL e cria extensão PGVector se necessário"""
        try:
            import os
            # Sempre usar variáveis de ambiente quando disponíveis (prioridade para Docker)
            # Se POSTGRES_HOST estiver definido nas variáveis de ambiente, usar ele
            env_host = os.getenv("POSTGRES_HOST")
            if env_host:
                # Usar valores do ambiente (Docker ou .env)
                user = os.getenv("POSTGRES_USER", "agente")
                password = os.getenv("POSTGRES_PASSWORD", "agente123")
                host = env_host
                port = os.getenv("POSTGRES_PORT", "5432")  # Porta padrão dentro do Docker
                database = os.getenv("POSTGRES_DB", "agente_db")
                conn_str = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            else:
                # Fallback para configuração do config.py
                conn_str = config.database.connection_string
                if "localhost" in conn_str:
                    conn_str = conn_str.replace("localhost", "127.0.0.1")
                # Garantir que está usando usuário 'agente' do .env
                if "marcodamo" in conn_str or "@127.0.0.1" in conn_str.split("@")[0]:
                    # Reconstruir connection string com valores corretos
                    user = os.getenv("POSTGRES_USER", "agente")
                    password = os.getenv("POSTGRES_PASSWORD", "agente123")
                    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
                    port = os.getenv("POSTGRES_PORT", "5433")
                    database = os.getenv("POSTGRES_DB", "agente_db")
                    conn_str = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            
            self.engine = create_engine(conn_str)
            self.SessionLocal = sessionmaker(bind=self.engine)
            
            # Testar conexão
            with self.engine.connect() as conn:
                # Verificar qual PostgreSQL estamos conectados
                try:
                    version_result = conn.execute(text("SELECT version()"))
                    version = version_result.fetchone()[0]
                    logger.info(f"Conectado ao PostgreSQL: {version[:50]}...")
                    
                    # Verificar usuário
                    user_result = conn.execute(text("SELECT current_user"))
                    current_user = user_result.fetchone()[0]
                    logger.info(f"Usuário atual: {current_user}")
                    
                    # Verificar se extensão vector está disponível
                    try:
                        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                        conn.commit()
                        logger.info("Extensão pgvector criada/verificada com sucesso")
                    except Exception as ext_error:
                        error_msg = str(ext_error)
                        if "vector" in error_msg.lower() and "not available" in error_msg.lower():
                            raise ValueError(
                                "Extensão pgvector não está disponível. "
                                "Certifique-se de que está usando PostgreSQL do Docker (docker-compose up -d) "
                                "que já inclui pgvector. Erro: " + error_msg
                            )
                        raise
                except Exception as test_error:
                    logger.error(f"Erro ao testar conexão: {test_error}")
                    raise
            
            # Criar tabela de documentos se não existir
            self._create_tables()
            
        except ValueError:
            # Re-raise ValueError com mensagem clara
            raise
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
    
    def _create_tables(self):
        """Cria tabelas necessárias para armazenar documentos vetorizados"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id SERIAL PRIMARY KEY,
            document_id VARCHAR(255) NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector(1536),
            metadata JSONB,
            source VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(document_id, chunk_index)
        );
        
        CREATE TABLE IF NOT EXISTS rag_metadata_fields (
            id SERIAL PRIMARY KEY,
            field_key VARCHAR(255) NOT NULL UNIQUE,
            field_label VARCHAR(255) NOT NULL,
            field_type VARCHAR(50) NOT NULL DEFAULT 'text',
            field_options JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
        ON document_chunks 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        
        CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx 
        ON document_chunks(document_id);
        
        CREATE INDEX IF NOT EXISTS rag_metadata_fields_key_idx 
        ON rag_metadata_fields(field_key);
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
    
    async def add_document(
        self,
        file_path: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        selected_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Processa e adiciona um documento à base de conhecimento
        
        Args:
            file_path: Caminho do arquivo a ser processado
            document_id: ID único do documento (gerado se não fornecido)
            metadata: Metadados adicionais do documento (chunk_index, document_id, etc.)
            selected_metadata: Metadata selecionada dos campos configurados (ex: {"departamento": "TI"})
            
        Returns:
            ID do documento adicionado
        """
        try:
            # Processar documento em chunks
            chunks = await self.document_processor.process_document(file_path)
            
            if not document_id:
                document_id = str(uuid.uuid4())
            
            # Obter todos os campos de metadata disponíveis
            try:
                available_fields = await self.list_metadata_fields()
                field_keys = {field["field_key"] for field in available_fields if field and isinstance(field, dict) and "field_key" in field}
            except Exception as e:
                logger.warning(f"Erro ao listar campos de metadata: {e}. Continuando sem campos de metadata.")
                field_keys = set()
            
            # Preparar metadata final: incluir selected_metadata e garantir que todos os campos disponíveis estejam presentes
            final_metadata = {}
            
            # Adicionar campos de metadata disponíveis
            for field_key in field_keys:
                if selected_metadata and isinstance(selected_metadata, dict) and field_key in selected_metadata:
                    final_metadata[field_key] = selected_metadata[field_key]
                else:
                    final_metadata[field_key] = None  # null se não selecionado
            
            # Adicionar metadata adicional (chunk_index, document_id, etc.)
            if metadata:
                final_metadata.update(metadata)
            
            # Gerar embeddings para cada chunk
            session = self.SessionLocal()
            try:
                for i, chunk in enumerate(chunks):
                    # Gerar embedding
                    embedding = await self.embedding_service.embed_text(chunk["content"])
                    
                    # Converter para formato PostgreSQL
                    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
                    
                    # Inserir no banco
                    # Usar bindparam para garantir que os tipos sejam tratados corretamente
                    from sqlalchemy import bindparam
                    
                    chunk_metadata = {
                        **final_metadata,
                        "chunk_index": i,
                        "document_id": document_id
                    }
                    
                    # Garantir que todos os campos de metadata disponíveis estejam no chunk_metadata
                    for field_key in field_keys:
                        if field_key not in chunk_metadata:
                            chunk_metadata[field_key] = None
                    
                    # Usar SQL direto com placeholders do psycopg2
                    insert_sql = text("""
                        INSERT INTO document_chunks 
                        (document_id, chunk_index, content, embedding, metadata, source)
                        VALUES (:doc_id, :chunk_idx, :content, CAST(:embedding AS vector), CAST(:metadata AS jsonb), :source)
                        ON CONFLICT (document_id, chunk_index) 
                        DO UPDATE SET 
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata
                    """)
                    
                    session.execute(insert_sql, {
                        "doc_id": document_id,
                        "chunk_idx": i,
                        "content": chunk["content"],
                        "embedding": embedding_str,
                        "metadata": json.dumps(chunk_metadata),
                        "source": chunk.get("source", file_path)
                    })
                
                session.commit()
                logger.info(f"Documento {document_id} adicionado com {len(chunks)} chunks")
                return document_id
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Erro ao adicionar documento: {e}", exc_info=True)
            raise
    
    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca documentos relevantes para uma consulta
        
        Args:
            query: Texto da consulta
            top_k: Número de resultados a retornar
            similarity_threshold: Limite mínimo de similaridade
            metadata_filter: Filtros de metadata (ex: {"departamento": "TI"})
            
        Returns:
            Lista de documentos relevantes com conteúdo e metadados
        """
        try:
            top_k = top_k or config.rag.top_k
            similarity_threshold = similarity_threshold or config.rag.similarity_threshold
            
            # Gerar embedding da query
            query_embedding = await self.embedding_service.embed_text(query)
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
            
            # Construir filtros de metadata na query SQL
            metadata_conditions = []
            query_params = {
                "query_embedding": embedding_str,
                "threshold": similarity_threshold,
                "top_k": top_k
            }
            
            if metadata_filter:
                for idx, (field_key, field_value) in enumerate(metadata_filter.items()):
                    if field_value is not None:  # Ignorar valores None
                        param_name = f"metadata_value_{idx}"
                        # Filtrar usando JSONB: metadata->>'field_key' = value
                        metadata_conditions.append(f"metadata->>'{field_key}' = :{param_name}")
                        query_params[param_name] = str(field_value)
            
            # Construir WHERE clause
            where_clauses = ["1 - (embedding <=> CAST(:query_embedding AS vector)) >= :threshold"]
            where_clauses.extend(metadata_conditions)
            where_clause = " AND ".join(where_clauses)
            
            # Buscar chunks similares usando cosine similarity
            # Usar CAST para converter string para vector
            search_sql = text(f"""
                SELECT 
                    content,
                    metadata,
                    source,
                    document_id,
                    1 - (embedding <=> CAST(:query_embedding AS vector)) as similarity
                FROM document_chunks
                WHERE {where_clause}
                ORDER BY embedding <=> CAST(:query_embedding AS vector)
                LIMIT :top_k
            """)
            
            session = self.SessionLocal()
            try:
                results = session.execute(search_sql, query_params).fetchall()
                
                return [
                    {
                        "content": row.content,
                        "source": row.source,
                        "document_id": row.document_id,
                        "similarity": float(row.similarity),
                        "metadata": row.metadata
                    }
                    for row in results
                ]
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Erro ao buscar documentos: {e}", exc_info=True)
            return []
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """
        Lista todos os documentos na base de conhecimento
        
        Returns:
            Lista de documentos com informações agregadas
        """
        try:
            session = self.SessionLocal()
            try:
                list_sql = text("""
                    SELECT 
                        document_id,
                        COUNT(*) as chunk_count,
                        MIN(created_at) as created_at,
                        MAX(created_at) as updated_at,
                        MAX(source) as source,
                        MAX(metadata->>'original_filename') as filename
                    FROM document_chunks
                    GROUP BY document_id
                    ORDER BY created_at DESC
                """)
                
                results = session.execute(list_sql).fetchall()
                
                documents = []
                for row in results:
                    documents.append({
                        "document_id": row.document_id,
                        "chunk_count": row.chunk_count,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                        "source": row.source,
                        "filename": row.filename or "N/A"
                    })
                
                return documents
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Erro ao listar documentos: {e}", exc_info=True)
            raise
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Remove um documento da base de conhecimento
        
        Args:
            document_id: ID do documento a ser removido
            
        Returns:
            True se o documento foi removido com sucesso
        """
        try:
            session = self.SessionLocal()
            try:
                # Verificar se documento existe
                check_sql = text("SELECT COUNT(*) FROM document_chunks WHERE document_id = :doc_id")
                count = session.execute(check_sql, {"doc_id": document_id}).scalar()
                
                if count == 0:
                    logger.warning(f"Documento {document_id} não encontrado")
                    return False
                
                # Deletar todos os chunks do documento
                delete_sql = text("DELETE FROM document_chunks WHERE document_id = :doc_id")
                result = session.execute(delete_sql, {"doc_id": document_id})
                session.commit()
                
                deleted_count = result.rowcount
                logger.info(f"Documento {document_id} removido ({deleted_count} chunks deletados)")
                return True
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Erro ao remover documento: {e}", exc_info=True)
            raise
    
    async def list_metadata_fields(self) -> List[Dict[str, Any]]:
        """
        Lista todos os campos de metadata disponíveis
        
        Returns:
            Lista de campos de metadata configurados
        """
        try:
            session = self.SessionLocal()
            try:
                list_sql = text("""
                    SELECT 
                        id,
                        field_key,
                        field_label,
                        field_type,
                        field_options,
                        created_at,
                        updated_at
                    FROM rag_metadata_fields
                    ORDER BY field_label
                """)
                
                results = session.execute(list_sql).fetchall()
                
                fields = []
                for row in results:
                    fields.append({
                        "id": row.id,
                        "field_key": row.field_key,
                        "field_label": row.field_label,
                        "field_type": row.field_type,
                        "field_options": row.field_options,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "updated_at": row.updated_at.isoformat() if row.updated_at else None
                    })
                
                return fields
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Erro ao listar campos de metadata: {e}", exc_info=True)
            raise
    
    async def create_metadata_field(
        self,
        field_key: str,
        field_label: str,
        field_type: str = "text",
        field_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Cria um novo campo de metadata
        
        Args:
            field_key: Chave única do campo (ex: "departamento", "categoria")
            field_label: Label amigável (ex: "Departamento", "Categoria")
            field_type: Tipo do campo (text, number, select, date, etc.)
            field_options: Opções adicionais (para select, validações, etc.)
            
        Returns:
            Campo criado
        """
        try:
            session = self.SessionLocal()
            try:
                # Criar campo
                insert_sql = text("""
                    INSERT INTO rag_metadata_fields 
                    (field_key, field_label, field_type, field_options)
                    VALUES (:field_key, :field_label, :field_type, CAST(:field_options AS jsonb))
                    ON CONFLICT (field_key) 
                    DO UPDATE SET 
                        field_label = EXCLUDED.field_label,
                        field_type = EXCLUDED.field_type,
                        field_options = EXCLUDED.field_options,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id, field_key, field_label, field_type, field_options, created_at, updated_at
                """)
                
                result = session.execute(insert_sql, {
                    "field_key": field_key,
                    "field_label": field_label,
                    "field_type": field_type,
                    "field_options": json.dumps(field_options) if field_options else None
                }).fetchone()
                
                session.commit()
                
                # Atualizar todos os documentos existentes: adicionar null para o novo campo
                # Usar jsonb_set para garantir que o campo seja adicionado mesmo se metadata for null
                update_sql = text("""
                    UPDATE document_chunks
                    SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(:field_key, NULL::jsonb)
                    WHERE metadata IS NULL OR metadata->>:field_key IS NULL
                """)
                
                session.execute(update_sql, {"field_key": field_key})
                session.commit()
                
                logger.info(f"Campo de metadata '{field_key}' criado e aplicado a documentos existentes")
                
                return {
                    "id": result.id,
                    "field_key": result.field_key,
                    "field_label": result.field_label,
                    "field_type": result.field_type,
                    "field_options": result.field_options,
                    "created_at": result.created_at.isoformat() if result.created_at else None,
                    "updated_at": result.updated_at.isoformat() if result.updated_at else None
                }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Erro ao criar campo de metadata: {e}", exc_info=True)
            raise
    
    async def delete_metadata_field(self, field_key: str) -> bool:
        """
        Remove um campo de metadata
        
        Args:
            field_key: Chave do campo a ser removido
            
        Returns:
            True se removido com sucesso
        """
        try:
            session = self.SessionLocal()
            try:
                # Remover campo de todos os documentos
                update_sql = text("""
                    UPDATE document_chunks
                    SET metadata = metadata - :field_key
                    WHERE metadata ? :field_key
                """)
                
                session.execute(update_sql, {"field_key": field_key})
                
                # Remover campo da tabela
                delete_sql = text("DELETE FROM rag_metadata_fields WHERE field_key = :field_key")
                result = session.execute(delete_sql, {"field_key": field_key})
                session.commit()
                
                deleted = result.rowcount > 0
                if deleted:
                    logger.info(f"Campo de metadata '{field_key}' removido")
                
                return deleted
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Erro ao remover campo de metadata: {e}", exc_info=True)
            raise
    
    async def update_document_metadata(
        self,
        document_id: str,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """
        Atualiza metadata de todos os chunks de um documento
        
        Args:
            document_id: ID do documento
            metadata_updates: Dicionário com campos de metadata a atualizar
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            session = self.SessionLocal()
            try:
                # Verificar se documento existe
                check_sql = text("SELECT COUNT(*) FROM document_chunks WHERE document_id = :doc_id")
                count = session.execute(check_sql, {"doc_id": document_id}).scalar()
                
                if count == 0:
                    logger.warning(f"Documento {document_id} não encontrado")
                    return False
                
                # Atualizar metadata de todos os chunks do documento
                # Atualizar múltiplos campos de uma vez usando jsonb_build_object
                metadata_json = json.dumps(metadata_updates)
                update_sql = text("""
                    UPDATE document_chunks
                    SET metadata = COALESCE(metadata, '{}'::jsonb) || CAST(:metadata_updates AS jsonb)
                    WHERE document_id = :doc_id
                """)
                
                session.execute(update_sql, {
                    "doc_id": document_id,
                    "metadata_updates": metadata_json
                })
                
                session.commit()
                logger.info(f"Metadata do documento {document_id} atualizada ({count} chunks)")
                return True
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Erro ao atualizar metadata do documento: {e}", exc_info=True)
            raise
    
    async def update_chunk_metadata(
        self,
        document_id: str,
        chunk_index: int,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """
        Atualiza metadata de um chunk específico
        
        Args:
            document_id: ID do documento
            chunk_index: Índice do chunk
            metadata_updates: Dicionário com campos de metadata a atualizar
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            session = self.SessionLocal()
            try:
                # Verificar se chunk existe
                check_sql = text("""
                    SELECT COUNT(*) FROM document_chunks 
                    WHERE document_id = :doc_id AND chunk_index = :chunk_idx
                """)
                count = session.execute(check_sql, {
                    "doc_id": document_id,
                    "chunk_idx": chunk_index
                }).scalar()
                
                if count == 0:
                    logger.warning(f"Chunk {document_id}:{chunk_index} não encontrado")
                    return False
                
                # Buscar metadata atual
                get_sql = text("""
                    SELECT metadata FROM document_chunks
                    WHERE document_id = :doc_id AND chunk_index = :chunk_idx
                """)
                result = session.execute(get_sql, {
                    "doc_id": document_id,
                    "chunk_idx": chunk_index
                }).fetchone()
                
                # Atualizar metadata
                current_metadata = result.metadata if result.metadata else {}
                if not isinstance(current_metadata, dict):
                    current_metadata = json.loads(current_metadata) if current_metadata else {}
                
                # Atualizar campos
                current_metadata.update(metadata_updates)
                
                # Salvar
                update_sql = text("""
                    UPDATE document_chunks
                    SET metadata = CAST(:metadata AS jsonb)
                    WHERE document_id = :doc_id AND chunk_index = :chunk_idx
                """)
                
                session.execute(update_sql, {
                    "doc_id": document_id,
                    "chunk_idx": chunk_index,
                    "metadata": json.dumps(current_metadata)
                })
                
                session.commit()
                logger.info(f"Metadata do chunk {document_id}:{chunk_index} atualizada")
                return True
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Erro ao atualizar metadata do chunk: {e}", exc_info=True)
            raise
    
    async def get_chunk_metadata(
        self,
        document_id: str,
        chunk_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém metadata de um chunk específico
        
        Args:
            document_id: ID do documento
            chunk_index: Índice do chunk
            
        Returns:
            Metadata do chunk ou None se não encontrado
        """
        try:
            session = self.SessionLocal()
            try:
                get_sql = text("""
                    SELECT metadata FROM document_chunks
                    WHERE document_id = :doc_id AND chunk_index = :chunk_idx
                """)
                result = session.execute(get_sql, {
                    "doc_id": document_id,
                    "chunk_idx": chunk_index
                }).fetchone()
                
                if result and result.metadata:
                    if isinstance(result.metadata, dict):
                        return result.metadata
                    return json.loads(result.metadata)
                
                return None
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Erro ao obter metadata do chunk: {e}", exc_info=True)
            raise
    
    async def get_document_chunks(
        self,
        document_id: str
    ) -> List[Dict[str, Any]]:
        """
        Lista todos os chunks de um documento
        
        Args:
            document_id: ID do documento
            
        Returns:
            Lista de chunks com metadata
        """
        try:
            session = self.SessionLocal()
            try:
                list_sql = text("""
                    SELECT 
                        chunk_index,
                        content,
                        metadata,
                        source,
                        created_at
                    FROM document_chunks
                    WHERE document_id = :doc_id
                    ORDER BY chunk_index
                """)
                
                results = session.execute(list_sql, {"doc_id": document_id}).fetchall()
                
                chunks = []
                for row in results:
                    metadata = row.metadata
                    if metadata and not isinstance(metadata, dict):
                        metadata = json.loads(metadata)
                    
                    chunks.append({
                        "chunk_index": row.chunk_index,
                        "content": row.content[:200] + "..." if len(row.content) > 200 else row.content,  # Preview
                        "content_full": row.content,
                        "metadata": metadata or {},
                        "source": row.source,
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    })
                
                return chunks
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Erro ao listar chunks do documento: {e}", exc_info=True)
            raise
    
