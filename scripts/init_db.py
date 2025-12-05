"""
Script para inicializar banco de dados e criar tabelas necessárias
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.rag.rag_service import RAGService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Inicializa o banco de dados"""
    try:
        logger.info("Inicializando banco de dados...")
        rag_service = RAGService()
        logger.info("Banco de dados inicializado com sucesso!")
        logger.info("Tabela document_chunks criada e extensão pgvector habilitada.")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

