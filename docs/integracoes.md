# Integrações

O sistema suporta integrações com múltiplas plataformas e serviços externos.

## WhatsApp (Evolution API)

### Configuração

1. Obtenha credenciais da Evolution API
2. Configure no `.env`:

```env
EVOLUTION_API_URL=https://api.evolutionapi.com
EVOLUTION_API_KEY=sua_chave_evolution_aqui
EVOLUTION_INSTANCE_NAME=sua_instancia
EVOLUTION_WEBHOOK_URL=https://seu-dominio.com/webhook/whatsapp
```

### Funcionalidades

- **Envio de mensagens de texto**
- **Envio de mídia** (imagens, vídeos, documentos)
- **Recebimento de mensagens** via webhook
- **Marcar mensagens como lidas**

### Configurar Webhook

Na Evolution API, configure o webhook para:
```
URL: https://seu-dominio.com/webhook/whatsapp
Método: POST
```

### Exemplo de Uso

```python
from src.modules.whatsapp.whatsapp_service import WhatsAppService

service = WhatsAppService()

# Enviar mensagem de texto
await service.send_text_message(
    phone_number="5511999999999",
    message="Olá! Como posso ajudar?"
)

# Enviar imagem
await service.send_media_message(
    phone_number="5511999999999",
    media_url="https://exemplo.com/imagem.jpg",
    media_type="image",
    caption="Veja esta imagem"
)
```

### Formato de Números

Use o formato internacional sem caracteres especiais:
- Correto: `5511999999999`
- Incorreto: `+55 11 99999-9999` ou `(11) 99999-9999`

---

## Calendly

### Configuração

1. Crie uma conta no Calendly
2. Obtenha sua API Key em: https://calendly.com/integrations/api_webhooks
3. Configure no `.env`:

```env
CALENDLY_API_KEY=sua_chave_calendly_aqui
CALENDLY_WEBHOOK_SECRET=seu_webhook_secret_aqui
CALENDLY_BASE_URL=https://api.calendly.com
```

### Funcionalidades

- **Buscar horários disponíveis**
- **Criar agendamentos**
- **Cancelar agendamentos**
- **Receber eventos** via webhook

### Configurar Webhook

No Calendly, configure o webhook para:
```
URL: https://seu-dominio.com/webhook/calendly
Eventos: event.created, event.canceled
```

### Exemplo de Uso

```python
from src.modules.calendly.calendly_service import CalendlyService
from datetime import datetime

service = CalendlyService()

# Buscar horários disponíveis
horarios = await service.get_available_times(
    event_type_uri="https://api.calendly.com/event_types/ABC123",
    start_time=datetime.now()
)

# Criar agendamento
evento = await service.create_event(
    event_type_uri="https://api.calendly.com/event_types/ABC123",
    invitee_name="João Silva",
    invitee_email="joao@exemplo.com",
    start_time=datetime(2024, 1, 15, 14, 0)
)
```

### Tools LangChain

O agente pode usar automaticamente as ferramentas Calendly quando o usuário solicita agendamento:

- `calendly_search_available_times` - Busca horários
- `calendly_create_event` - Cria agendamento

---

## Voz (Speech-to-Text e Text-to-Speech)

### Provedores Suportados

#### Google Cloud Speech/TTS

**Configuração:**

1. Crie um projeto no Google Cloud
2. Habilite as APIs: Cloud Speech-to-Text e Cloud Text-to-Speech
3. Crie uma conta de serviço e baixe o arquivo JSON de credenciais
4. Configure no `.env`:

```env
VOICE_PROVIDER=google
VOICE_LANGUAGE_CODE=pt-BR
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credentials.json
```

#### AWS Transcribe/Polly

**Configuração:**

```env
VOICE_PROVIDER=aws
VOICE_LANGUAGE_CODE=pt-BR
AWS_ACCESS_KEY_ID=sua_chave_aws
AWS_SECRET_ACCESS_KEY=sua_secret_aws
```

#### ElevenLabs

**Configuração:**

```env
VOICE_PROVIDER=elevenlabs
VOICE_LANGUAGE_CODE=pt-BR
ELEVENLABS_API_KEY=sua_chave_elevenlabs
```

### Exemplo de Uso

```python
from src.modules.voice.voice_service import VoiceService

service = VoiceService()

# Speech-to-Text (converter áudio em texto)
with open("audio.wav", "rb") as f:
    audio_data = f.read()

texto = await service.speech_to_text(
    audio_data=audio_data,
    sample_rate=16000,
    encoding="LINEAR16"
)

# Text-to-Speech (converter texto em áudio)
audio_bytes = await service.text_to_speech(
    text="Olá, como posso ajudar?",
    voice_name="pt-BR-Standard-A"
)

with open("resposta.wav", "wb") as f:
    f.write(audio_bytes)
```

---

## OpenAI (GPT-4o)

### Configuração

```env
OPENAI_API_KEY=sua_chave_openai_aqui
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

### Modelos Disponíveis

- `gpt-4o` (padrão) - Mais recente e poderoso
- `gpt-4-turbo` - Alternativa rápida
- `gpt-3.5-turbo` - Mais econômico

---

## PostgreSQL + PGVector (RAG)

### Configuração

O PostgreSQL é iniciado automaticamente via Docker Compose. Configure apenas se usar instância externa:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=agente
POSTGRES_PASSWORD=agente123
POSTGRES_DB=agente_db
```

### Embeddings

Configure o provedor de embeddings:

```env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

**Provedores suportados:**
- `openai` - Usa OpenAI Embeddings API
- `sentence-transformers` - Modelos locais (ex: `paraphrase-multilingual-MiniLM-L12-v2`)

---

## Redis

### Configuração

O Redis é iniciado automaticamente via Docker Compose. Configure apenas se usar instância externa:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

### Uso

O Redis é usado para:
- Cache de conversas
- Memória de curto prazo
- Armazenamento de perfis de usuários

---

## Adicionar Nova Integração

Para adicionar uma nova integração:

1. Crie um novo módulo em `src/modules/nova_integracao/`
2. Crie a classe de serviço seguindo o padrão dos outros módulos
3. Adicione configurações em `src/config/config.py`
4. Registre o módulo no orquestrador se necessário
5. Crie tools LangChain se o agente precisar usar a integração

**Exemplo de estrutura:**

```python
# src/modules/nova_integracao/nova_integracao_service.py
from src.config.config import config

class NovaIntegracaoService:
    def __init__(self):
        self.api_key = config.nova_integracao.api_key
    
    async def fazer_algo(self):
        # Implementação
        pass
```

