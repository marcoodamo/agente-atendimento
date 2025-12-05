# Guia de Instalação

## Pré-requisitos

- **Python 3.10+**
- **Docker e Docker Compose** (para PostgreSQL e Redis)
- **OpenAI API Key** (para GPT-4o)
- **Git** (para clonar o repositório)

## Instalação Passo a Passo

### 1. Clonar o Repositório

```bash
git clone <url-do-repositorio>
cd agente-atendimento
```

### 2. Criar Ambiente Virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instalar Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# API e Autenticação
API_KEY=sua_chave_secreta_aqui
ENABLE_API_AUTH=true

# OpenAI
OPENAI_API_KEY=sua_chave_openai_aqui
LLM_MODEL=gpt-4o

# Banco de Dados
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433  # Porta 5433 para evitar conflito com PostgreSQL local
POSTGRES_USER=agente
POSTGRES_PASSWORD=agente123
POSTGRES_DB=agente_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# WhatsApp (Evolution API) - Opcional
EVOLUTION_API_URL=https://api.evolutionapi.com
EVOLUTION_API_KEY=sua_chave_evolution_aqui
EVOLUTION_INSTANCE_NAME=sua_instancia

# Calendly - Opcional
CALENDLY_API_KEY=sua_chave_calendly_aqui

# Voz - Opcional
VOICE_PROVIDER=google
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credentials.json
```

### 5. Iniciar Serviços Docker

**Importante**: Docker Desktop deve estar rodando antes de executar este comando.

```bash
# Verificar se Docker está rodando
docker ps

# Se não estiver, inicie Docker Desktop primeiro
# No Mac: Abra o aplicativo Docker Desktop e aguarde inicializar

# Iniciar serviços
docker-compose up -d
```

Isso inicia:
- PostgreSQL com extensão PGVector na porta **5433** (para evitar conflito com PostgreSQL local)
- Redis na porta 6379

**Troubleshooting Docker:**
- Se ver erro "Cannot connect to Docker daemon": Inicie Docker Desktop primeiro
- Se porta 5433 estiver em uso: Verifique com `lsof -i :5433`
- Para ver logs: `docker-compose logs postgres`

### 6. Criar Banco de Dados

```bash
source venv/bin/activate
python scripts/create_db.py
```

Este script:
- Cria o banco de dados `agente_db`
- Habilita a extensão `pgvector`
- Configura usuário e senha

**Nota**: Se o script falhar, você pode criar manualmente:
```bash
docker exec -it agente-postgres psql -U agente -c "CREATE DATABASE agente_db;"
docker exec -it agente-postgres psql -U agente -d agente_db -c "CREATE EXTENSION vector;"
```

### 7. Inicializar Banco de Dados (RAG)

```bash
python scripts/init_db.py
```

Este script cria as tabelas para o módulo RAG.

### 8. Verificar Instalação

```bash
python scripts/check_setup.py
```

Este script verifica se todas as dependências e configurações estão corretas.

## Comandos Rápidos

### Instalação de Dependências

```bash
# Manual (criar venv e instalar dependências)
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Erros comuns:**
- `command not found: pip` → Use `python -m pip` ao invés de `pip`
- `externally-managed-environment` → Ative o venv primeiro: `source venv/bin/activate`

### Iniciar Serviços

```bash
# 1. Iniciar Docker (se ainda não iniciou)
docker-compose up -d

# 2. Criar banco de dados (primeira vez)
python scripts/create_db.py
python scripts/init_db.py

# 3. Iniciar API
source venv/bin/activate
export $(grep -v '^#' .env | xargs)
export POSTGRES_PORT=5433
export ENABLE_KNOWLEDGE=true
python -m src.main --mode api --port 8000

# 4. Iniciar Interface (em outro terminal, apenas se não usar Docker)
source venv/bin/activate
streamlit run interface.py --server.port 8501
```

### Script Automático (Recomendado)

```bash
./start.sh
```

Este script:
1. Verifica Docker e inicia se necessário
2. Verifica/cria arquivo .env
3. Inicia todos os serviços via Docker Compose
4. Mostra status e URLs de acesso
3. Inicia API com RAG habilitado
4. Inicia Interface Streamlit

## Iniciar o Servidor

### Modo API (Produção)

```bash
source venv/bin/activate
export $(grep -v '^#' .env | xargs)
export POSTGRES_PORT=5433
export ENABLE_KNOWLEDGE=true
python -m src.main --mode api --port 8000
```

### Modo CLI (Teste)

```bash
python -m src.main --mode cli
```

### Modo Teste

```bash
python -m src.main --mode test
```

## Verificação

Após iniciar o servidor, teste a API:

```bash
# Health check
curl http://localhost:8000/health

# Informações do serviço
curl http://localhost:8000/

# Processar mensagem (requer API Key)
curl -X POST http://localhost:8000/api/message \
  -H "X-API-Key: sua_chave_aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Olá, teste",
    "user_id": "test_user",
    "channel": "api"
  }'
```

## Problemas Comuns

### Erro: "OPENAI_API_KEY não configurada"

Certifique-se de que o arquivo `.env` existe e contém `OPENAI_API_KEY=sua_chave`.

### Erro: "database agente_db does not exist"

Execute `python scripts/create_db.py` para criar o banco.

### Erro: "extension vector is not available"

Certifique-se de que está usando o PostgreSQL do Docker (`docker-compose up -d`), que já inclui pgvector.

### Porta 8000 já em uso

Use outra porta:
```bash
python -m src.main --mode api --port 8001
```

## Próximos Passos

Após a instalação, consulte:
- [APIs](apis.md) - Documentação da API
- [Integrações](integracoes.md) - Como configurar integrações
- [Edição](edicao.md) - Como customizar o sistema

