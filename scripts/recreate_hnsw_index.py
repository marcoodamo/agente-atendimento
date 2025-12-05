"""
Script para recriar o índice HNSW no PostgreSQL
Útil quando o índice precisa ser recriado ou atualizado
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from src.config.config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def recreate_hnsw_index():
    """Recria o índice HNSW"""
    try:
        engine = create_engine(config.database.connection_string)
        
        with engine.connect() as conn:
            # Remover índice antigo se existir (pode ser IVFFlat)
            logger.info("Removendo índices antigos...")
            conn.execute(text("DROP INDEX IF EXISTS document_chunks_embedding_idx"))
            conn.commit()
            
            # Criar novo índice HNSW
            logger.info("Criando índice HNSW...")
            create_index_sql = """
            CREATE INDEX document_chunks_embedding_idx 
            ON document_chunks 
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
            """
            
            conn.execute(text(create_index_sql))
            conn.commit()
            
            logger.info("Índice HNSW criado com sucesso!")
            
            # Verificar índice criado
            check_sql = """
            SELECT 
                indexname, 
                indexdef 
            FROM pg_indexes 
            WHERE tablename = 'document_chunks' 
            AND indexname = 'document_chunks_embedding_idx';
            """
            
            result = conn.execute(text(check_sql)).fetchone()
            if result:
                logger.info(f"Índice verificado: {result.indexname}")
                logger.info(f"Definição: {result.indexdef}")
            
    except Exception as e:
        logger.error(f"Erro ao recriar índice: {e}")
        raise


if __name__ == "__main__":
    recreate_hnsw_index()

