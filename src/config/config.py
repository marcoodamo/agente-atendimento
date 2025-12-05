"""
Gerenciamento de configurações do agente
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseConfig(BaseSettings):
    """Configurações do banco de dados"""
    host: str = Field(default="127.0.0.1", env="POSTGRES_HOST")  # Usar 127.0.0.1 para forçar IPv4 e conectar ao Docker
    port: int = Field(default=5433, env="POSTGRES_PORT")  # Porta 5433 para conectar ao Docker (evita conflito com PostgreSQL local)
    user: str = Field(default="agente", env="POSTGRES_USER")
    password: str = Field(default="agente123", env="POSTGRES_PASSWORD")
    database: str = Field(default="agente_db", env="POSTGRES_DB")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Forçar uso do .env se a variável não foi definida explicitamente
        env_file = Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key == "POSTGRES_USER" and "POSTGRES_USER" not in os.environ:
                            object.__setattr__(self, "user", value)
                        elif key == "POSTGRES_PASSWORD" and "POSTGRES_PASSWORD" not in os.environ:
                            object.__setattr__(self, "password", value)
                        elif key == "POSTGRES_HOST" and "POSTGRES_HOST" not in os.environ:
                            object.__setattr__(self, "host", value)
                        elif key == "POSTGRES_PORT" and "POSTGRES_PORT" not in os.environ:
                            object.__setattr__(self, "port", int(value))
                        elif key == "POSTGRES_DB" and "POSTGRES_DB" not in os.environ:
                            object.__setattr__(self, "database", value)
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class LLMConfig(BaseSettings):
    """Configurações do modelo de linguagem"""
    provider: str = Field(default="openai", env="LLM_PROVIDER")
    model: str = Field(default="gpt-4o", env="LLM_MODEL")  # OpenAI 4.1 (gpt-4o é a versão mais recente)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")


class EmbeddingConfig(BaseSettings):
    """Configurações de embeddings"""
    provider: str = Field(default="openai", env="EMBEDDING_PROVIDER")
    model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    dimension: int = Field(default=1536, env="EMBEDDING_DIMENSION")


class WhatsAppConfig(BaseSettings):
    """Configurações do WhatsApp (Evolution API)"""
    api_url: str = Field(default="https://api.evolutionapi.com", env="EVOLUTION_API_URL")
    api_key: Optional[str] = Field(default=None, env="EVOLUTION_API_KEY")
    instance_name: Optional[str] = Field(default=None, env="EVOLUTION_INSTANCE_NAME")
    webhook_url: Optional[str] = Field(default=None, env="EVOLUTION_WEBHOOK_URL")


class CalendlyConfig(BaseSettings):
    """Configurações do Calendly"""
    api_key: Optional[str] = Field(default=None, env="CALENDLY_API_KEY")
    webhook_secret: Optional[str] = Field(default=None, env="CALENDLY_WEBHOOK_SECRET")
    base_url: str = Field(default="https://api.calendly.com", env="CALENDLY_BASE_URL")


class VoiceConfig(BaseSettings):
    """Configurações de voz (ASR/TTS)"""
    provider: str = Field(default="google", env="VOICE_PROVIDER")
    language_code: str = Field(default="pt-BR", env="VOICE_LANGUAGE_CODE")
    google_credentials_path: Optional[str] = Field(default=None, env="GOOGLE_APPLICATION_CREDENTIALS")
    aws_access_key: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    elevenlabs_api_key: Optional[str] = Field(default=None, env="ELEVENLABS_API_KEY")


class RAGConfig(BaseSettings):
    """Configurações do RAG"""
    top_k: int = Field(default=5, env="RAG_TOP_K")
    similarity_threshold: float = Field(default=0.3, env="RAG_SIMILARITY_THRESHOLD")  # Reduzido de 0.7 para 0.3 para melhorar recall
    chunk_size: int = Field(default=1000, env="RAG_CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="RAG_CHUNK_OVERLAP")


class RedisConfig(BaseSettings):
    """Configurações do Redis"""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")
    decode_responses: bool = Field(default=True, env="REDIS_DECODE_RESPONSES")
    
    @property
    def connection_url(self) -> str:
        """Retorna URL de conexão do Redis"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class APIConfig(BaseSettings):
    """Configurações da API"""
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    enable_auth: bool = Field(default=True, env="ENABLE_API_AUTH")
    api_title: str = Field(default="Agente IA Multicanal", env="API_TITLE")
    api_version: str = Field(default="0.1.0", env="API_VERSION")


class AgentConfig(BaseSettings):
    """Configurações gerais do agente"""
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    environment: str = Field(default="development", env="ENVIRONMENT")
    max_conversation_history: int = Field(default=20, env="MAX_CONVERSATION_HISTORY")
    
    # Configurações de memória
    recent_messages_count: int = Field(default=5, env="RECENT_MESSAGES_COUNT")
    enable_conversation_summary: bool = Field(default=True, env="ENABLE_CONVERSATION_SUMMARY")
    summary_update_threshold: int = Field(default=10, env="SUMMARY_UPDATE_THRESHOLD")  # Atualizar sumário a cada N mensagens
    
    # Module flags
    enable_agendamento: bool = Field(default=True, env="ENABLE_AGENDAMENTO")
    enable_followup: bool = Field(default=True, env="ENABLE_FOLLOWUP")
    enable_voz: bool = Field(default=True, env="ENABLE_VOZ")
    enable_knowledge: bool = Field(default=True, env="ENABLE_KNOWLEDGE")
    enable_transbordo_humano: bool = Field(default=True, env="ENABLE_TRANSBORDO_HUMANO")
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    config_dir: Path = base_dir / "src" / "config"
    data_dir: Path = base_dir / "data"
    uploads_dir: Path = data_dir / "uploads"
    vectors_dir: Path = data_dir / "vectors"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Criar diretórios se não existirem
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.vectors_dir.mkdir(parents=True, exist_ok=True)


class Config(BaseSettings):
    """Configuração principal do sistema"""
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    api: APIConfig = APIConfig()
    llm: LLMConfig = LLMConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    whatsapp: WhatsAppConfig = WhatsAppConfig()
    calendly: CalendlyConfig = CalendlyConfig()
    voice: VoiceConfig = VoiceConfig()
    rag: RAGConfig = RAGConfig()
    agent: AgentConfig = AgentConfig()
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # Ignorar variáveis extras do .env
    }


# Instância global de configuração
# Carregar .env manualmente antes de criar Config para garantir que variáveis sejam lidas
import os
from pathlib import Path

env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Só definir se não estiver já definido no ambiente (variáveis exportadas têm prioridade)
                if key not in os.environ:
                    os.environ[key] = value

config = Config()

