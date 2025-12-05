"""
Serviço de processamento de voz (Speech-to-Text e Text-to-Speech)
"""
import logging
from typing import Optional, BinaryIO
import asyncio

from src.config.config import config

logger = logging.getLogger(__name__)


class VoiceService:
    """
    Serviço para processar áudio (ASR) e gerar áudio (TTS)
    """
    
    def __init__(self):
        self.provider = config.voice.provider.lower()
        self.language_code = config.voice.language_code
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Inicializa clientes de ASR e TTS"""
        if self.provider == "google":
            self._init_google_clients()
        elif self.provider == "aws":
            self._init_aws_clients()
        elif self.provider == "elevenlabs":
            self._init_elevenlabs_client()
        else:
            raise ValueError(f"Provedor de voz não suportado: {self.provider}")
    
    def _init_google_clients(self):
        """Inicializa clientes Google Cloud Speech e Text-to-Speech"""
        try:
            from google.cloud import speech_v1
            from google.cloud import texttospeech_v1
            
            if config.voice.google_credentials_path:
                import os
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.voice.google_credentials_path
            
            self.speech_client = speech_v1.SpeechClient()
            self.tts_client = texttospeech_v1.TextToSpeechClient()
            logger.info("Clientes Google Cloud Speech/TTS inicializados")
        except ImportError:
            raise ImportError("google-cloud-speech e google-cloud-texttospeech devem ser instalados")
        except Exception as e:
            logger.error(f"Erro ao inicializar Google Cloud: {e}")
            raise
    
    def _init_aws_clients(self):
        """Inicializa clientes AWS Transcribe e Polly"""
        try:
            import boto3
            
            if not config.voice.aws_access_key or not config.voice.aws_secret_key:
                raise ValueError("Credenciais AWS não configuradas")
            
            self.transcribe_client = boto3.client(
                'transcribe',
                aws_access_key_id=config.voice.aws_access_key,
                aws_secret_access_key=config.voice.aws_secret_key,
                region_name='us-east-1'
            )
            self.polly_client = boto3.client(
                'polly',
                aws_access_key_id=config.voice.aws_access_key,
                aws_secret_access_key=config.voice.aws_secret_key,
                region_name='us-east-1'
            )
            logger.info("Clientes AWS Transcribe/Polly inicializados")
        except ImportError:
            raise ImportError("boto3 deve ser instalado para usar AWS")
        except Exception as e:
            logger.error(f"Erro ao inicializar AWS: {e}")
            raise
    
    def _init_elevenlabs_client(self):
        """Inicializa cliente ElevenLabs"""
        try:
            from elevenlabs import ElevenLabs
            
            if not config.voice.elevenlabs_api_key:
                raise ValueError("ElevenLabs API key não configurada")
            
            self.elevenlabs_client = ElevenLabs(api_key=config.voice.elevenlabs_api_key)
            logger.info("Cliente ElevenLabs inicializado")
        except ImportError:
            raise ImportError("elevenlabs deve ser instalado")
        except Exception as e:
            logger.error(f"Erro ao inicializar ElevenLabs: {e}")
            raise
    
    async def speech_to_text(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        encoding: str = "LINEAR16"
    ) -> str:
        """
        Converte áudio em texto (Speech-to-Text)
        
        Args:
            audio_data: Dados de áudio em bytes
            sample_rate: Taxa de amostragem (Hz)
            encoding: Formato de codificação do áudio
            
        Returns:
            Texto transcrito
        """
        try:
            if self.provider == "google":
                return await self._google_speech_to_text(audio_data, sample_rate, encoding)
            elif self.provider == "aws":
                return await self._aws_speech_to_text(audio_data, sample_rate, encoding)
            else:
                raise ValueError(f"ASR não implementado para {self.provider}")
        except Exception as e:
            logger.error(f"Erro no Speech-to-Text: {e}")
            raise
    
    async def _google_speech_to_text(
        self,
        audio_data: bytes,
        sample_rate: int,
        encoding: str
    ) -> str:
        """Google Cloud Speech-to-Text"""
        from google.cloud.speech_v1 import RecognitionConfig, RecognitionAudio
        
        config_speech = RecognitionConfig(
            encoding=RecognitionConfig.AudioEncoding.LINEAR16 if encoding == "LINEAR16" else RecognitionConfig.AudioEncoding.OGG_OPUS,
            sample_rate_hertz=sample_rate,
            language_code=self.language_code,
        )
        
        audio = RecognitionAudio(content=audio_data)
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.speech_client.recognize(config=config_speech, audio=audio)
        )
        
        if response.results:
            return response.results[0].alternatives[0].transcript
        return ""
    
    async def _aws_speech_to_text(
        self,
        audio_data: bytes,
        sample_rate: int,
        encoding: str
    ) -> str:
        """AWS Transcribe Speech-to-Text"""
        # AWS Transcribe requer arquivo em S3 ou streaming
        # Implementação simplificada - em produção usar streaming ou S3
        import uuid
        import tempfile
        
        # Salvar temporariamente e processar
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(audio_data)
            tmp_file_path = tmp_file.name
        
        try:
            job_name = f"transcribe-{uuid.uuid4()}"
            # Upload e processamento (implementação completa requer S3)
            # Por enquanto, retornar placeholder
            logger.warning("AWS Transcribe requer implementação completa com S3")
            return ""
        finally:
            import os
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    async def text_to_speech(
        self,
        text: str,
        voice_name: Optional[str] = None,
        gender: str = "NEUTRAL"
    ) -> bytes:
        """
        Converte texto em áudio (Text-to-Speech)
        
        Args:
            text: Texto a ser convertido
            voice_name: Nome da voz a usar (opcional)
            gender: Gênero da voz (MALE, FEMALE, NEUTRAL)
            
        Returns:
            Dados de áudio em bytes
        """
        try:
            if self.provider == "google":
                return await self._google_text_to_speech(text, voice_name, gender)
            elif self.provider == "aws":
                return await self._aws_text_to_speech(text, voice_name, gender)
            elif self.provider == "elevenlabs":
                return await self._elevenlabs_text_to_speech(text, voice_name)
            else:
                raise ValueError(f"TTS não implementado para {self.provider}")
        except Exception as e:
            logger.error(f"Erro no Text-to-Speech: {e}")
            raise
    
    async def _google_text_to_speech(
        self,
        text: str,
        voice_name: Optional[str],
        gender: str
    ) -> bytes:
        """Google Cloud Text-to-Speech"""
        from google.cloud.texttospeech_v1 import SynthesisInput, VoiceSelectionParams, AudioConfig
        
        input_text = SynthesisInput(text=text)
        
        # Selecionar voz
        voice = VoiceSelectionParams(
            language_code=self.language_code,
            ssml_gender=(
                self.tts_client.SsmlVoiceGender.MALE if gender == "MALE"
                else self.tts_client.SsmlVoiceGender.FEMALE if gender == "FEMALE"
                else self.tts_client.SsmlVoiceGender.NEUTRAL
            )
        )
        
        if voice_name:
            voice.name = voice_name
        
        audio_config = AudioConfig(audio_encoding=self.tts_client.AudioEncoding.MP3)
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.tts_client.synthesize_speech(
                input=input_text,
                voice=voice,
                audio_config=audio_config
            )
        )
        
        return response.audio_content
    
    async def _aws_text_to_speech(
        self,
        text: str,
        voice_name: Optional[str],
        gender: str
    ) -> bytes:
        """AWS Polly Text-to-Speech"""
        voice_id = voice_name or ("Vitoria" if gender == "FEMALE" else "Ricardo")
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                LanguageCode='pt-BR'
            )
        )
        
        return response['AudioStream'].read()
    
    async def _elevenlabs_text_to_speech(
        self,
        text: str,
        voice_name: Optional[str]
    ) -> bytes:
        """ElevenLabs Text-to-Speech"""
        voice_id = voice_name or "21m00Tcm4TlvDq8ikWAM"  # Voz padrão
        
        loop = asyncio.get_event_loop()
        audio_generator = await loop.run_in_executor(
            None,
            lambda: self.elevenlabs_client.generate(
                text=text,
                voice=voice_id
            )
        )
        
        # Converter generator para bytes
        audio_bytes = b"".join(audio_generator)
        return audio_bytes

