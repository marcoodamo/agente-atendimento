# Arquitetura do Sistema

## Visão Geral

O Agente IA Multicanal é construído com uma arquitetura modular que permite ativar/desativar funcionalidades conforme necessário. O sistema é composto por:

1. **Núcleo (Core)**: Orquestrador principal e gerenciamento de contexto
2. **Módulos**: Funcionalidades específicas (WhatsApp, Voz, RAG, Calendly, Follow-up)
3. **API**: Endpoints REST e webhooks
4. **Configuração**: Gerenciamento centralizado de configurações e prompts

## Componentes Principais

### 1. Core (Núcleo)

#### `AgentOrchestrator`
- Coordena todos os módulos
- Processa mensagens do usuário
- Detecta intenções
- Gera respostas usando LLM (GPT-4o via LangChain)
- Gerencia fluxo de conversação

**Localização**: `src/core/orchestrator.py`

#### `ConversationMemory`
- Armazena histórico de conversas
- Mantém contexto de curto e longo prazo
- Gerencia perfis de usuários
- Usa Redis para persistência

**Localização**: `src/core/memory.py`

#### `LangChainAgent`
- Integração com LangChain
- Processamento inteligente de mensagens
- Uso de tools (ferramentas) quando necessário
- Geração de respostas contextualizadas

**Localização**: `src/core/langchain_agent.py`

#### `PromptManager`
- Carrega e gerencia prompt fixo do sistema
- Adiciona instruções extras dinamicamente
- Permite atualização de prompts sem reiniciar

**Localização**: `src/core/prompt_manager.py`

### 2. Módulos

#### RAG (Retrieval-Augmented Generation)
- **RAGService**: Gerencia busca vetorial e recuperação
- **EmbeddingService**: Gera embeddings de texto
- **DocumentProcessor**: Processa documentos (PDF, DOCX, TXT) em chunks

**Tecnologias**:
- PostgreSQL com extensão PGVector
- Modelos de embedding (OpenAI ou sentence-transformers)

**Localização**: `src/modules/rag/`

#### WhatsApp
- **WhatsAppService**: Integração com Evolution API
- Envio/recebimento de mensagens
- Processamento de webhooks
- Suporte a mídia

**Localização**: `src/modules/whatsapp/`

#### Voz
- **VoiceService**: Processamento de áudio
- Speech-to-Text (ASR)
- Text-to-Speech (TTS)
- Suporte a múltiplos provedores (Google, AWS, ElevenLabs)

**Localização**: `src/modules/voice/`

#### Calendly
- **CalendlyService**: Integração com Calendly API
- Busca de horários disponíveis
- Criação de eventos
- Cancelamento de agendamentos
- Processamento de webhooks

**Localização**: `src/modules/calendly/`

#### Follow-up
- **FollowUpService**: Gerenciamento de follow-ups
- Agendamento de mensagens automáticas
- Diferentes tipos de follow-up (pós-serviço, lembretes, etc.)

**Localização**: `src/modules/followup/`

### 3. API

#### `webhook_server.py`
- Servidor FastAPI
- Endpoints REST
- Webhooks para integrações externas
- Autenticação via API Key

**Endpoints principais**:
- `POST /api/message` - Processar mensagem
- `POST /webhook/whatsapp` - Webhook WhatsApp
- `POST /webhook/calendly` - Webhook Calendly
- `GET /api/rag/search` - Buscar na base de conhecimento
- `POST /api/rag/add-document` - Adicionar documento

**Localização**: `src/api/webhook_server.py`

## Fluxo de Processamento

### Processamento de Mensagem

1. **Recebimento**: Mensagem chega via API ou webhook
2. **Recuperação de Contexto**: Sistema busca histórico do usuário
3. **Busca RAG** (se ativo): Busca informações relevantes na base de conhecimento
4. **Processamento LangChain**: 
   - Agente analisa a mensagem
   - Decide quais tools usar (se necessário)
   - Executa tools (ex: buscar horários Calendly)
   - Gera resposta usando GPT-4o
5. **Salvamento**: Resposta salva na memória
6. **Resposta**: Retorna resposta ao usuário

### Integração com Módulos

Os módulos são ativados/desativados via:
- Flags de linha de comando (`--agendamento`, `--followup`, etc.)
- Variáveis de ambiente (`ENABLE_AGENDAMENTO`, `ENABLE_FOLLOWUP`, etc.)
- Configuração em `config.yaml`

## Tecnologias Utilizadas

- **Python 3.10+**
- **LangChain 1.1.0** - Framework para agentes IA
- **OpenAI GPT-4o** - Modelo de linguagem
- **FastAPI** - Framework web assíncrono
- **PostgreSQL + PGVector** - Banco de dados vetorial
- **Redis** - Cache e memória de conversas
- **SQLAlchemy** - ORM para banco de dados
- **Pydantic** - Validação de dados

## Estrutura de Diretórios

```
agente-atendimento/
├── src/
│   ├── core/              # Núcleo do agente
│   │   ├── orchestrator.py
│   │   ├── langchain_agent.py
│   │   ├── memory.py
│   │   └── prompt_manager.py
│   ├── modules/           # Módulos funcionais
│   │   ├── whatsapp/
│   │   ├── voice/
│   │   ├── rag/
│   │   ├── calendly/
│   │   └── followup/
│   ├── api/               # API e webhooks
│   ├── config/            # Configurações
│   └── utils/             # Utilitários
├── docs/                  # Documentação
├── scripts/               # Scripts utilitários
└── docker-compose.yml     # Infraestrutura
```

## Escalabilidade

O sistema foi projetado para escalar:
- **Stateless API**: Cada requisição é independente
- **Redis**: Cache compartilhado para múltiplas instâncias
- **PostgreSQL**: Banco de dados relacional escalável
- **Async/Await**: Processamento assíncrono para melhor performance

## Segurança

- Autenticação via API Key
- Validação de dados com Pydantic
- Sanitização de inputs
- Logs estruturados para auditoria

