# Módulo de Voz

O módulo de voz permite atendimento telefônico através de Speech-to-Text (ASR) e Text-to-Speech (TTS).

## Visão Geral

O sistema suporta múltiplos provedores de voz:
- **Google Cloud** - Speech-to-Text e Text-to-Speech
- **AWS** - Transcribe e Polly
- **ElevenLabs** - Text-to-Speech de alta qualidade

## Configuração

### Habilitar Módulo

No arquivo `.env`:
```env
ENABLE_VOZ=true
```

Ou via linha de comando:
```bash
python -m src.main --mode api --voz
```

## Google Cloud Speech/TTS

### Pré-requisitos

1. Criar projeto no Google Cloud Platform
2. Habilitar APIs:
   - Cloud Speech-to-Text API
   - Cloud Text-to-Speech API
3. Criar conta de serviço e baixar credenciais JSON

### Configuração

```env
VOICE_PROVIDER=google
VOICE_LANGUAGE_CODE=pt-BR
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credentials.json
```

### Exemplo de Uso

```python
from src.modules.voice.voice_service import VoiceService

service = VoiceService()

# Speech-to-Text
with open("audio.wav", "rb") as f:
    audio_data = f.read()

texto = await service.speech_to_text(
    audio_data=audio_data,
    sample_rate=16000,
    encoding="LINEAR16"
)
print(f"Texto transcrito: {texto}")

# Text-to-Speech
audio_bytes = await service.text_to_speech(
    text="Olá, como posso ajudar?",
    voice_name="pt-BR-Standard-A"
)

with open("resposta.wav", "wb") as f:
    f.write(audio_bytes)
```

### Vozes Disponíveis (pt-BR)

- `pt-BR-Standard-A` - Voz feminina padrão
- `pt-BR-Standard-B` - Voz masculina padrão
- `pt-BR-Wavenet-A` - Voz feminina neural (melhor qualidade)
- `pt-BR-Wavenet-B` - Voz masculina neural

---

## AWS Transcribe/Polly

### Pré-requisitos

1. Conta AWS
2. Credenciais de acesso (Access Key ID e Secret Access Key)
3. Permissões para Transcribe e Polly

### Configuração

```env
VOICE_PROVIDER=aws
VOICE_LANGUAGE_CODE=pt-BR
AWS_ACCESS_KEY_ID=sua_chave_aws
AWS_SECRET_ACCESS_KEY=sua_secret_aws
```

### Exemplo de Uso

```python
from src.modules.voice.voice_service import VoiceService

service = VoiceService()

# Speech-to-Text (AWS Transcribe)
texto = await service.speech_to_text(
    audio_data=audio_bytes,
    sample_rate=16000,
    encoding="LINEAR16"
)

# Text-to-Speech (AWS Polly)
audio_bytes = await service.text_to_speech(
    text="Olá, como posso ajudar?",
    voice_name="Camila"  # Voz brasileira
)
```

### Vozes Disponíveis (pt-BR)

- `Camila` - Voz feminina
- `Vitoria` - Voz feminina alternativa
- `Ricardo` - Voz masculina

---

## ElevenLabs

### Pré-requisitos

1. Conta ElevenLabs
2. API Key

### Configuração

```env
VOICE_PROVIDER=elevenlabs
VOICE_LANGUAGE_CODE=pt-BR
ELEVENLABS_API_KEY=sua_chave_elevenlabs
```

### Exemplo de Uso

```python
from src.modules.voice.voice_service import VoiceService

service = VoiceService()

# Text-to-Speech (ElevenLabs)
audio_bytes = await service.text_to_speech(
    text="Olá, como posso ajudar?",
    voice_name="voice_id_aqui"
)
```

**Nota:** ElevenLabs é apenas para TTS. Para ASR, use Google ou AWS.

---

## Formatos de Áudio Suportados

### Speech-to-Text

- **LINEAR16** (PCM 16-bit) - Recomendado
- **FLAC** - Alta qualidade
- **MULAW** - Telefonia
- **AMR** - Mobile

### Text-to-Speech

- **WAV** - Padrão
- **MP3** - Compacto
- **OGG** - Open source

## Integração com Atendimento

### Fluxo Completo de Atendimento por Voz

```python
from src.modules.voice.voice_service import VoiceService
from src.core.orchestrator import AgentOrchestrator

voice_service = VoiceService()
orchestrator = AgentOrchestrator()

# 1. Receber áudio do cliente
audio_input = await receber_audio_do_telefone()

# 2. Converter áudio em texto (ASR)
texto_cliente = await voice_service.speech_to_text(
    audio_data=audio_input,
    sample_rate=16000,
    encoding="LINEAR16"
)

# 3. Processar mensagem com o agente
resposta = await orchestrator.process_message(
    user_message=texto_cliente,
    user_id="telefone_5511999999999",
    channel="voice"
)

# 4. Converter resposta em áudio (TTS)
audio_resposta = await voice_service.text_to_speech(
    text=resposta["response"],
    voice_name="pt-BR-Standard-A"
)

# 5. Enviar áudio de volta ao cliente
await enviar_audio_para_telefone(audio_resposta)
```

## Processamento de Áudio

### Pré-processamento

Antes de enviar para ASR, pode ser necessário:

```python
from pydub import AudioSegment

# Converter formato
audio = AudioSegment.from_file("entrada.mp3")
audio = audio.set_frame_rate(16000)  # 16kHz
audio = audio.set_channels(1)  # Mono
audio = audio.set_sample_width(2)  # 16-bit

# Exportar como WAV
audio.export("saida.wav", format="wav")
```

### Pós-processamento

Após receber do TTS:

```python
from pydub import AudioSegment

# Converter para formato desejado
audio = AudioSegment.from_wav("resposta.wav")
audio.export("resposta.mp3", format="mp3", bitrate="128k")
```

## Otimização

### Cache de Respostas

Para respostas frequentes, cache o áudio:

```python
import hashlib
import os

def get_cached_audio(text: str) -> Optional[bytes]:
    cache_key = hashlib.md5(text.encode()).hexdigest()
    cache_path = f"cache/audio/{cache_key}.wav"
    
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return f.read()
    return None

def cache_audio(text: str, audio: bytes):
    cache_key = hashlib.md5(text.encode()).hexdigest()
    cache_path = f"cache/audio/{cache_key}.wav"
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    with open(cache_path, "wb") as f:
        f.write(audio)
```

### Streaming

Para respostas longas, use streaming:

```python
# Google Cloud TTS com streaming
async def text_to_speech_streaming(text: str):
    from google.cloud import texttospeech_v1
    
    client = texttospeech_v1.TextToSpeechClient()
    
    synthesis_input = texttospeech_v1.SynthesisInput(text=text)
    voice = texttospeech_v1.VoiceSelectionParams(
        language_code="pt-BR",
        name="pt-BR-Standard-A"
    )
    audio_config = texttospeech_v1.AudioConfig(
        audio_encoding=texttospeech_v1.AudioEncoding.MP3
    )
    
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    
    return response.audio_content
```

## Custos

### Google Cloud

- **Speech-to-Text**: ~$0.006 por 15 segundos
- **Text-to-Speech**: ~$0.004 por 1.000 caracteres

### AWS

- **Transcribe**: ~$0.0004 por segundo
- **Polly**: ~$0.000004 por caractere

### ElevenLabs

- Depende do plano (gratuito limitado)

## Troubleshooting

### Erro: "Credenciais não encontradas"

Verifique se o arquivo de credenciais está no caminho correto e tem permissões de leitura.

### Erro: "Formato de áudio não suportado"

Converta o áudio para um formato suportado (WAV, FLAC, etc.) e verifique sample_rate e encoding.

### Latência Alta

- Use modelos mais rápidos (Standard ao invés de Wavenet)
- Reduza sample_rate se possível
- Use cache para respostas frequentes

### Qualidade de Áudio Ruim

- Use sample_rate mais alto (44100 Hz)
- Use formato sem perda (WAV, FLAC)
- Verifique qualidade do áudio de entrada

