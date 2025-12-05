# Documentação da API

## Base URL

```
http://localhost:8000
```

## Autenticação

A maioria dos endpoints requer autenticação via **API Key** no header:

```
X-API-Key: sua_chave_aqui
```

Configure a API Key no arquivo `.env`:
```env
API_KEY=sua_chave_secreta_aqui
ENABLE_API_AUTH=true
```

## Endpoints

### 1. Health Check

Verifica se o serviço está funcionando (não requer autenticação).

**GET** `/health`

**Resposta:**
```json
{
    "status": "healthy"
}
```

**Exemplo:**
```bash
curl http://localhost:8000/health
```

---

### 2. Informações do Serviço

Retorna informações sobre o serviço (não requer autenticação).

**GET** `/`

**Resposta:**
```json
{
    "service": "Agente IA Multicanal",
    "status": "running",
    "version": "0.1.0",
    "authentication": "API Key required"
}
```

---

### 3. Processar Mensagem

Processa uma mensagem do usuário e retorna a resposta do agente IA.

**POST** `/api/message`

**Headers:**
```
X-API-Key: sua_chave_aqui
Content-Type: application/json
```

**Body:**
```json
{
    "message": "Olá, preciso de ajuda",
    "user_id": "user123",
    "channel": "api",
    "metadata": {
        "name": "João Silva",
        "phone": "+5511999999999"
    }
}
```

**Resposta:**
```json
{
    "response": "Olá! Como posso ajudá-lo hoje?",
    "sources": ["documento1.pdf"],
    "timestamp": "2024-01-15T10:30:00.000Z",
    "agent_steps": []
}
```

**Exemplo:**
```bash
curl -X POST http://localhost:8000/api/message \
  -H "X-API-Key: sua_chave_aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quais são seus horários de atendimento?",
    "user_id": "user123",
    "channel": "api"
  }'
```

---

### 4. Buscar na Base de Conhecimento (RAG)

Busca documentos relevantes na base de conhecimento usando busca vetorial.

**GET** `/api/rag/search`

**Query Parameters:**
- `query` (obrigatório): Query de busca
- `top_k` (opcional): Número de resultados (padrão: 5, máximo: 20)

**Headers:**
```
X-API-Key: sua_chave_aqui
```

**Resposta:**
```json
{
    "results": [
        {
            "content": "Texto do documento...",
            "source": "documento.pdf",
            "score": 0.95
        }
    ]
}
```

**Exemplo:**
```bash
curl "http://localhost:8000/api/rag/search?query=horários&top_k=3" \
  -H "X-API-Key: sua_chave_aqui"
```

---

### 5. Adicionar Documento (RAG)

Adiciona um documento à base de conhecimento.

**POST** `/api/rag/add-document`

**Headers:**
```
X-API-Key: sua_chave_aqui
Content-Type: application/json
```

**Body:**
```json
{
    "file_path": "/caminho/para/documento.pdf",
    "document_id": "doc_123"
}
```

**Resposta:**
```json
{
    "status": "success",
    "document_id": "doc_123"
}
```

**Formatos suportados:** PDF, DOCX, TXT

**Exemplo:**
```bash
curl -X POST http://localhost:8000/api/rag/add-document \
  -H "X-API-Key: sua_chave_aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/caminho/para/documento.pdf"
  }'
```

---

### 6. Webhook WhatsApp

Recebe mensagens do WhatsApp via Evolution API.

**POST** `/webhook/whatsapp`

**Body:** (formato da Evolution API)

**Resposta:**
```json
{
    "status": "processed",
    "response": "Resposta enviada ao usuário"
}
```

**Nota:** Configure o webhook na Evolution API apontando para `https://seu-dominio.com/webhook/whatsapp`

---

### 7. Webhook Calendly

Recebe eventos do Calendly.

**POST** `/webhook/calendly`

**Body:** (formato do Calendly)

**Resposta:**
```json
{
    "status": "processed"
}
```

**Nota:** Configure o webhook no Calendly apontando para `https://seu-dominio.com/webhook/calendly`

## Documentação Interativa

A documentação completa da API está disponível em:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Códigos de Status HTTP

- `200 OK` - Requisição bem-sucedida
- `400 Bad Request` - Dados inválidos
- `401 Unauthorized` - API Key não fornecida
- `403 Forbidden` - API Key inválida
- `500 Internal Server Error` - Erro interno do servidor

## Rate Limiting

Atualmente não há rate limiting implementado. Para produção, recomenda-se adicionar rate limiting (ex: usando `slowapi`).

## Exemplos de Integração

### Python

```python
import httpx

async def enviar_mensagem(mensagem: str, user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/message",
            headers={
                "X-API-Key": "sua_chave_aqui",
                "Content-Type": "application/json"
            },
            json={
                "message": mensagem,
                "user_id": user_id,
                "channel": "api"
            }
        )
        return response.json()
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

async function enviarMensagem(mensagem, userId) {
    const response = await axios.post(
        'http://localhost:8000/api/message',
        {
            message: mensagem,
            user_id: userId,
            channel: 'api'
        },
        {
            headers: {
                'X-API-Key': 'sua_chave_aqui',
                'Content-Type': 'application/json'
            }
        }
    );
    return response.data;
}
```

### cURL

```bash
#!/bin/bash

API_KEY="sua_chave_aqui"
API_URL="http://localhost:8000"

# Processar mensagem
curl -X POST "$API_URL/api/message" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Olá",
    "user_id": "user123",
    "channel": "api"
  }'
```

