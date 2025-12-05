"""
Processador de documentos - Extrai texto e divide em chunks
"""
import logging
from typing import List, Dict
from pathlib import Path
import asyncio

from src.config.config import config

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Processa documentos e os divide em chunks para indexação
    """
    
    def __init__(self):
        self.chunk_size = config.rag.chunk_size
        self.chunk_overlap = config.rag.chunk_overlap
    
    async def process_document(self, file_path: str) -> List[Dict[str, str]]:
        """
        Processa um documento e retorna chunks de texto
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Lista de chunks com conteúdo e metadados
        """
        file_path_obj = Path(file_path)
        extension = file_path_obj.suffix.lower()
        
        # Extrair texto baseado na extensão
        if extension == ".txt":
            text = await self._read_text_file(file_path)
        elif extension == ".pdf":
            text = await self._read_pdf_file(file_path)
        elif extension in [".doc", ".docx"]:
            text = await self._read_docx_file(file_path)
        else:
            raise ValueError(f"Formato de arquivo não suportado: {extension}")
        
        # Dividir em chunks
        chunks = self._split_into_chunks(text, file_path)
        
        return chunks
    
    async def _read_text_file(self, file_path: str) -> str:
        """Lê arquivo de texto"""
        loop = asyncio.get_event_loop()
        with open(file_path, "r", encoding="utf-8") as f:
            return await loop.run_in_executor(None, f.read)
    
    async def _read_pdf_file(self, file_path: str) -> str:
        """Lê arquivo PDF"""
        try:
            from pypdf import PdfReader
            loop = asyncio.get_event_loop()
            
            def read_pdf():
                reader = PdfReader(file_path)
                text_parts = []
                for page in reader.pages:
                    text_parts.append(page.extract_text())
                return "\n".join(text_parts)
            
            return await loop.run_in_executor(None, read_pdf)
        except ImportError:
            raise ImportError("pypdf não instalado. Instale com: pip install pypdf")
    
    async def _read_docx_file(self, file_path: str) -> str:
        """Lê arquivo DOCX"""
        try:
            from docx import Document
            loop = asyncio.get_event_loop()
            
            def read_docx():
                doc = Document(file_path)
                paragraphs = [p.text for p in doc.paragraphs]
                return "\n".join(paragraphs)
            
            return await loop.run_in_executor(None, read_docx)
        except ImportError:
            raise ImportError("python-docx não instalado. Instale com: pip install python-docx")
    
    def _split_into_chunks(self, text: str, source: str) -> List[Dict[str, str]]:
        """
        Divide texto em chunks com overlap
        
        Args:
            text: Texto completo
            source: Fonte do documento
            
        Returns:
            Lista de chunks
        """
        chunks = []
        words = text.split()
        
        # Dividir em chunks de palavras (aproximadamente chunk_size caracteres)
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 para espaço
            
            if current_length + word_length > self.chunk_size and current_chunk:
                # Finalizar chunk atual
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "content": chunk_text,
                    "source": source
                })
                
                # Iniciar novo chunk com overlap
                overlap_words = int(self.chunk_overlap / 10)  # Aproximação
                current_chunk = current_chunk[-overlap_words:] + [word]
                current_length = sum(len(w) + 1 for w in current_chunk)
            else:
                current_chunk.append(word)
                current_length += word_length
        
        # Adicionar último chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "content": chunk_text,
                "source": source
            })
        
        return chunks

