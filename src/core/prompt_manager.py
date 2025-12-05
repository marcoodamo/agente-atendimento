"""
Gerenciador de prompts do sistema
Carrega e gerencia o prompt fixo e instruções extras
"""
import logging
from pathlib import Path
from typing import Optional

from src.config.config import config

logger = logging.getLogger(__name__)


class PromptManager:
    """
    Gerencia prompts do sistema e instruções extras
    """
    
    def __init__(self):
        self.system_prompt_path = config.agent.config_dir / "system_prompt.txt"
        self._system_prompt: Optional[str] = None
        self._load_system_prompt()
    
    def _load_system_prompt(self):
        """Carrega o prompt fixo do sistema"""
        try:
            if self.system_prompt_path.exists():
                with open(self.system_prompt_path, "r", encoding="utf-8") as f:
                    self._system_prompt = f.read()
            else:
                logger.warning(f"Arquivo de prompt não encontrado: {self.system_prompt_path}")
                self._system_prompt = self._get_default_prompt()
        except Exception as e:
            logger.error(f"Erro ao carregar prompt do sistema: {e}")
            self._system_prompt = self._get_default_prompt()
    
    def get_system_prompt(self) -> str:
        """Retorna o prompt fixo do sistema"""
        if not self._system_prompt:
            return self._get_default_prompt()
        return self._system_prompt
    
    def update_system_prompt(self, new_prompt: str):
        """
        Atualiza o prompt do sistema
        """
        try:
            with open(self.system_prompt_path, "w", encoding="utf-8") as f:
                f.write(new_prompt)
            self._system_prompt = new_prompt
            logger.info("Prompt do sistema atualizado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao atualizar prompt: {e}")
            raise
    
    def add_extra_instructions(
        self,
        base_prompt: str,
        extra_instructions: str
    ) -> str:
        """
        Adiciona instruções extras ao prompt base
        
        Args:
            base_prompt: Prompt base
            extra_instructions: Instruções adicionais a serem incluídas
            
        Returns:
            Prompt completo com instruções extras
        """
        if not extra_instructions:
            return base_prompt
        
        return f"{base_prompt}\n\n## Instruções Adicionais:\n{extra_instructions}"
    
    def _get_default_prompt(self) -> str:
        """Retorna um prompt padrão caso o arquivo não exista"""
        return """Você é um assistente virtual inteligente especializado em atendimento ao cliente.

Seja cordial, profissional e empático. Sempre tente ajudar o cliente da melhor forma possível.
Use informações da base de conhecimento quando disponíveis. Se não souber algo, seja honesto e ofereça alternativas.
Se necessário, ofereça transferência para um atendente humano."""

