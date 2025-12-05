"""
Script para adicionar documento à base de conhecimento
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.rag.rag_service import RAGService
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_document(file_path: str, document_id: str = None):
    """Adiciona documento à base de conhecimento"""
    try:
        rag_service = RAGService()
        doc_id = await rag_service.add_document(file_path, document_id)
        logger.info(f"Documento adicionado com sucesso! ID: {doc_id}")
        return doc_id
    except Exception as e:
        logger.error(f"Erro ao adicionar documento: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Adiciona documento à base de conhecimento")
    parser.add_argument("file_path", help="Caminho do arquivo a ser processado")
    parser.add_argument("--document-id", help="ID único do documento (opcional)")
    
    args = parser.parse_args()
    
    file_path = Path(args.file_path)
    if not file_path.exists():
        logger.error(f"Arquivo não encontrado: {file_path}")
        sys.exit(1)
    
    asyncio.run(add_document(str(file_path), args.document_id))


if __name__ == "__main__":
    main()

