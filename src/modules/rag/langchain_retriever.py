"""
Retriever LangChain para integração RAG
"""
import logging
from typing import List, Dict, Any

from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document

from src.modules.rag.rag_service import RAGService

logger = logging.getLogger(__name__)


class PGVectorRetriever(BaseRetriever):
    """
    Retriever LangChain que usa PostgreSQL + PGVector
    """
    
    def __init__(self, rag_service: RAGService, top_k: int = 5):
        super().__init__()
        self.rag_service = rag_service
        self.top_k = top_k
    
    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Busca documentos relevantes para a query
        """
        import asyncio
        
        try:
            # Executar busca assíncrona
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(
                self.rag_service.search(query, top_k=self.top_k)
            )
            
            # Converter para Document do LangChain
            documents = []
            for result in results:
                doc = Document(
                    page_content=result.get("content", ""),
                    metadata={
                        "source": result.get("source", ""),
                        "document_id": result.get("document_id", ""),
                        "similarity": result.get("similarity", 0.0)
                    }
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Erro ao buscar documentos: {e}")
            return []
    
    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Versão assíncrona da busca
        """
        try:
            results = await self.rag_service.search(query, top_k=self.top_k)
            
            documents = []
            for result in results:
                doc = Document(
                    page_content=result.get("content", ""),
                    metadata={
                        "source": result.get("source", ""),
                        "document_id": result.get("document_id", ""),
                        "similarity": result.get("similarity", 0.0)
                    }
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Erro ao buscar documentos: {e}")
            return []

