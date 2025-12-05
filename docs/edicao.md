# Edição e Customização

Guia completo para editar e customizar o sistema conforme suas necessidades.

## Personalizar Prompt do Sistema

O prompt do sistema define o comportamento e personalidade do agente.

**Arquivo:** `src/config/system_prompt.txt`

### Exemplo de Edição

```txt
Você é um assistente virtual da empresa XYZ, especializado em atendimento ao cliente.

## Personalidade
- Seja cordial e profissional
- Use linguagem clara e objetiva
- Demonstre empatia

## Diretrizes
- Sempre confirme informações importantes
- Se não souber algo, seja honesto
- Ofereça alternativas quando possível
```

**Após editar:** Reinicie o servidor para aplicar mudanças.

## Configurar Comportamento

### Arquivo de Configuração

**Arquivo:** `src/config/config.yaml`

```yaml
agent:
  log_level: INFO
  max_conversation_history: 20
  enable_agendamento: true
  enable_followup: true
  enable_voz: true
  enable_knowledge: true
```

### Variáveis de Ambiente

Configure no arquivo `.env`:

```env
# Comportamento do LLM
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Memória
MAX_CONVERSATION_HISTORY=20
RECENT_MESSAGES_COUNT=5
ENABLE_CONVERSATION_SUMMARY=true
```

## Adicionar Novas Ferramentas (Tools)

### Criar Tool LangChain

**Arquivo:** `src/core/langchain_tools.py`

```python
from langchain.tools import tool

@tool
def minha_nova_ferramenta(parametro: str) -> str:
    """
    Descrição da ferramenta que o agente verá.
    
    Args:
        parametro: Descrição do parâmetro
        
    Returns:
        Resultado da ferramenta
    """
    # Implementação
    resultado = fazer_algo(parametro)
    return resultado
```

### Registrar Tool

```python
# Em langchain_tools.py
def get_available_tools():
    tools = []
    
    # Tools existentes
    if config.agent.enable_agendamento:
        tools.extend([calendly_search_available_times, calendly_create_event])
    
    # Nova tool
    tools.append(minha_nova_ferramenta)
    
    return tools
```

## Customizar Respostas

### Interceptar e Modificar Respostas

**Arquivo:** `src/core/orchestrator.py`

```python
async def process_message(self, user_message: str, ...):
    # ... processamento normal ...
    
    response = result.get("response", "")
    
    # Customização antes de retornar
    response = self._customize_response(response, user_id)
    
    return {
        "response": response,
        ...
    }

def _customize_response(self, response: str, user_id: str) -> str:
    """Customiza resposta baseado no usuário"""
    # Exemplo: adicionar nome do usuário
    user_name = self.memory.get_user_name(user_id)
    if user_name:
        response = f"Olá {user_name}! {response}"
    
    return response
```

## Adicionar Novos Endpoints

**Arquivo:** `src/api/webhook_server.py`

```python
@app.get("/api/custom/endpoint")
async def meu_endpoint_customizado(
    api_key: str = Depends(api_key_auth.verify_api_key)
):
    """Descrição do endpoint"""
    return {"status": "success", "data": "resultado"}
```

## Modificar Fluxo de Processamento

### Adicionar Validações

**Arquivo:** `src/core/orchestrator.py`

```python
async def process_message(self, user_message: str, ...):
    # Validação customizada
    if not self._validate_message(user_message):
        return {
            "response": "Mensagem inválida",
            "error": "validation_failed"
        }
    
    # ... resto do processamento ...

def _validate_message(self, message: str) -> bool:
    """Valida mensagem antes de processar"""
    # Exemplo: verificar tamanho
    if len(message) > 1000:
        return False
    return True
```

## Customizar Memória

### Adicionar Campos Personalizados

**Arquivo:** `src/core/memory.py`

```python
async def add_message(self, user_id: str, role: str, content: str, ...):
    # ... código existente ...
    
    # Adicionar campo customizado
    message_data["custom_field"] = metadata.get("custom_field")
    
    # Salvar no Redis
    await self._save_message(user_id, message_data)
```

## Adicionar Novos Módulos

### Estrutura de Módulo

```
src/modules/meu_modulo/
├── __init__.py
└── meu_modulo_service.py
```

### Exemplo de Módulo

**Arquivo:** `src/modules/meu_modulo/meu_modulo_service.py`

```python
from src.config.config import config

class MeuModuloService:
    def __init__(self):
        self.api_key = config.meu_modulo.api_key
    
    async def fazer_algo(self, parametro: str):
        """Implementação do módulo"""
        pass
```

### Adicionar Configuração

**Arquivo:** `src/config/config.py`

```python
class MeuModuloConfig(BaseSettings):
    api_key: Optional[str] = Field(default=None, env="MEU_MODULO_API_KEY")

class Config(BaseSettings):
    # ... outras configurações ...
    meu_modulo: MeuModuloConfig = MeuModuloConfig()
```

### Registrar no Orquestrador

**Arquivo:** `src/core/orchestrator.py`

```python
def __init__(self):
    # ... código existente ...
    
    if config.agent.enable_meu_modulo:
        from src.modules.meu_modulo.meu_modulo_service import MeuModuloService
        self.meu_modulo_service = MeuModuloService()
```

## Customizar Logging

### Configurar Logs

**Arquivo:** `src/main.py`

```python
import logging
import structlog

# Logging estruturado
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

logger = structlog.get_logger()
```

## Adicionar Middleware

**Arquivo:** `src/api/webhook_server.py`

```python
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## Customizar Autenticação

**Arquivo:** `src/api/auth.py`

```python
class APIKeyAuth:
    async def verify_api_key(self, api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
        # Validação customizada
        if api_key and self._is_valid_key(api_key):
            return api_key
        raise HTTPException(status_code=403, detail="API Key inválida")
    
    def _is_valid_key(self, key: str) -> bool:
        # Lógica customizada de validação
        # Exemplo: verificar em banco de dados
        return key == self.api_key
```

## Adicionar Validações de Dados

**Arquivo:** `src/api/webhook_server.py`

```python
from pydantic import BaseModel, validator

class MessageRequest(BaseModel):
    message: str
    user_id: str
    channel: str
    
    @validator('message')
    def validate_message(cls, v):
        if len(v) < 1:
            raise ValueError('Mensagem não pode estar vazia')
        if len(v) > 5000:
            raise ValueError('Mensagem muito longa')
        return v
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or len(v) < 1:
            raise ValueError('user_id inválido')
        return v
```

## Customizar Tratamento de Erros

**Arquivo:** `src/api/webhook_server.py`

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "detail": str(exc) if config.agent.environment == "development" else None
        }
    )
```

## Adicionar Métricas

**Arquivo:** `src/api/webhook_server.py`

```python
from prometheus_client import Counter, Histogram

request_count = Counter('api_requests_total', 'Total de requisições')
request_duration = Histogram('api_request_duration_seconds', 'Duração das requisições')

@app.middleware("http")
async def track_metrics(request: Request, call_next):
    request_count.inc()
    with request_duration.time():
        response = await call_next(request)
    return response
```

## Exemplos de Customizações Comuns

### 1. Adicionar Saudação Personalizada

```python
def _add_greeting(self, response: str, user_id: str) -> str:
    """Adiciona saudação baseada no horário"""
    from datetime import datetime
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        greeting = "Bom dia"
    elif 12 <= hour < 18:
        greeting = "Boa tarde"
    else:
        greeting = "Boa noite"
    
    return f"{greeting}! {response}"
```

### 2. Filtrar Conteúdo Inadequado

```python
def _filter_content(self, message: str) -> str:
    """Filtra palavras inadequadas"""
    palavras_proibidas = ["palavra1", "palavra2"]
    
    for palavra in palavras_proibidas:
        message = message.replace(palavra, "***")
    
    return message
```

### 3. Adicionar Assinatura

```python
def _add_signature(self, response: str) -> str:
    """Adiciona assinatura à resposta"""
    signature = "\n\n---\nEquipe de Atendimento"
    return response + signature
```

## Boas Práticas

1. **Mantenha backups**: Faça backup antes de editar arquivos importantes
2. **Teste localmente**: Teste mudanças em ambiente de desenvolvimento primeiro
3. **Documente mudanças**: Documente customizações feitas
4. **Use versionamento**: Use Git para controlar versões
5. **Monitore logs**: Acompanhe logs após mudanças

## Recursos Adicionais

- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

