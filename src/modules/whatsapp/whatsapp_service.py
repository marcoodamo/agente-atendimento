"""
Serviço de integração com WhatsApp via Evolution API
"""
import logging
from typing import Dict, Optional, Any, List
import httpx

from src.config.config import config

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Serviço para interagir com WhatsApp através da Evolution API
    """
    
    def __init__(self):
        self.api_url = config.whatsapp.api_url
        self.api_key = config.whatsapp.api_key
        self.instance_name = config.whatsapp.instance_name
        
        if not self.api_key:
            logger.warning("Evolution API key não configurada")
        if not self.instance_name:
            logger.warning("Evolution API instance name não configurada")
    
    async def send_text_message(
        self,
        phone_number: str,
        message: str,
        quoted_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem de texto via WhatsApp
        
        Args:
            phone_number: Número do destinatário (formato: 5511999999999)
            message: Texto da mensagem
            quoted_message_id: ID da mensagem a ser citada (opcional)
            
        Returns:
            Resposta da API
        """
        try:
            url = f"{self.api_url}/message/sendText/{self.instance_name}"
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "number": phone_number,
                "text": message
            }
            
            if quoted_message_id:
                payload["quoted"] = {
                    "key": {
                        "remoteJid": f"{phone_number}@s.whatsapp.net",
                        "id": quoted_message_id
                    }
                }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem WhatsApp: {e}")
            raise
    
    async def send_media_message(
        self,
        phone_number: str,
        media_url: str,
        media_type: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem com mídia (imagem, vídeo, áudio, documento)
        
        Args:
            phone_number: Número do destinatário
            media_url: URL da mídia
            media_type: Tipo da mídia (image, video, audio, document)
            caption: Legenda (opcional)
            
        Returns:
            Resposta da API
        """
        try:
            url = f"{self.api_url}/message/sendMedia/{self.instance_name}"
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "number": phone_number,
                "media": media_url,
                "mediatype": media_type
            }
            
            if caption:
                payload["caption"] = caption
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Erro ao enviar mídia WhatsApp: {e}")
            raise
    
    async def mark_message_as_read(
        self,
        message_id: str,
        phone_number: str
    ) -> Dict[str, Any]:
        """
        Marca mensagem como lida
        
        Args:
            message_id: ID da mensagem
            phone_number: Número do remetente
        """
        try:
            url = f"{self.api_url}/chat/markMessageAsRead/{self.instance_name}"
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "read_messages": [{
                    "id": message_id,
                    "fromMe": False,
                    "remoteJid": f"{phone_number}@s.whatsapp.net"
                }]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Erro ao marcar mensagem como lida: {e}")
            raise
    
    def parse_webhook_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Processa dados recebidos do webhook da Evolution API
        
        Args:
            webhook_data: Dados do webhook
            
        Returns:
            Mensagem formatada ou None se não for mensagem válida
        """
        try:
            # Estrutura esperada da Evolution API v2
            event = webhook_data.get("event")
            data = webhook_data.get("data", {})
            
            if event != "messages.upsert":
                return None
            
            message_data = data.get("message", {})
            key = data.get("key", {})
            
            # Extrair informações
            phone_number = key.get("remoteJid", "").split("@")[0]
            message_id = key.get("id")
            from_me = key.get("fromMe", False)
            
            # Ignorar mensagens enviadas por nós mesmos
            if from_me:
                return None
            
            # Extrair conteúdo da mensagem
            content = None
            message_type = None
            
            # Verificar diferentes tipos de mensagem
            if "conversation" in message_data:
                content = message_data["conversation"]
                message_type = "text"
            elif "extendedTextMessage" in message_data:
                content = message_data["extendedTextMessage"].get("text", "")
                message_type = "text"
            elif "imageMessage" in message_data:
                content = message_data["imageMessage"].get("caption", "")
                message_type = "image"
            elif "videoMessage" in message_data:
                content = message_data["videoMessage"].get("caption", "")
                message_type = "video"
            elif "audioMessage" in message_data:
                message_type = "audio"
            elif "documentMessage" in message_data:
                content = message_data["documentMessage"].get("caption", "")
                message_type = "document"
            
            if not content and message_type == "text":
                return None
            
            return {
                "phone_number": phone_number,
                "message_id": message_id,
                "content": content or "",
                "type": message_type,
                "timestamp": data.get("messageTimestamp"),
                "raw_data": webhook_data
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}")
            return None
    
    async def get_instance_status(self) -> Dict[str, Any]:
        """
        Verifica status da instância WhatsApp
        """
        try:
            url = f"{self.api_url}/instance/fetchInstances"
            headers = {
                "apikey": self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                instances = response.json()
                
                # Encontrar nossa instância
                for instance in instances:
                    if instance.get("instanceName") == self.instance_name:
                        return instance
                
                return {"status": "not_found"}
                
        except Exception as e:
            logger.error(f"Erro ao verificar status: {e}")
            return {"status": "error", "error": str(e)}

