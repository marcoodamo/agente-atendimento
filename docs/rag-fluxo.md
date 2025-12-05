# Fluxo Completo do RAG - Upload e Busca

## Como Funciona o RAG Agora

O RAG (Retrieval-Augmented Generation) funciona em 4 etapas principais:

1. **Upload**: Arquivo é enviado via API
2. **Processamento**: Documento é dividido em chunks
3. **Indexação**: Chunks são convertidos em embeddings e armazenados com índice HNSW
4. **Busca**: Queries são convertidas em embeddings e comparadas usando busca vetorial

## 1. Upload de Arquivo

### Via API (Recomendado)

```bash
curl -X POST http://localhost:8000/api/rag/upload \
  -H "X-API-Key: sua_chave_aqui" \
  -F "file=@/caminho/para/documento.pdf" \
  -F "document_id=doc_123"
```

**Resposta:**
```json
{
    "status": "success",
    "document_id": "doc_123"
}
```

### Via Python

```python
import requests

url = "http://localhost:8000/api/rag/upload"
headers = {"X-API-Key": "sua_chave_aqui"}

with open("documento.pdf", "rb") as f:
    files = {"file": ("documento.pdf", f, "application/pdf")}
    data = {"document_id": "doc_123"}  # Opcional
    
    response = requests.post(url, headers=headers, files=files, data=data)
    print(response.json())
```

## 2. Processamento Interno

Quando você faz upload, o sistema:

1. **Salva o arquivo** em `data/uploads/`
2. **Processa o documento**:
   - PDF → Extrai texto de todas as páginas
   - DOCX → Extrai parágrafos
   - TXT → Lê diretamente
3. **Divide em chunks**:
   - Tamanho padrão: 1000 caracteres
   - Overlap: 200 caracteres (para manter contexto)
4. **Gera embeddings**:
   - Cada chunk vira um vetor de 1536 dimensões (OpenAI)
   - Ou dimensões do modelo escolhido
5. **Armazena no PostgreSQL**:
   - Tabela: `document_chunks`
   - Índice: **HNSW** (Hierarchical Navigable Small World)
   - Parâmetros: `m=16, ef_construction=64`

## 3. Índice HNSW

### Por que HNSW?

- **Mais rápido** que IVFFlat para buscas
- **Melhor qualidade** de resultados
- **Escalável** para grandes volumes de dados
- **Suporta inserções incrementais** sem reconstruir o índice

### Parâmetros HNSW

- **m = 16**: Número de conexões bidirecionais (mais = melhor qualidade, mais lento)
- **ef_construction = 64**: Tamanho da lista dinâmica durante construção (mais = melhor qualidade, mais lento)

### Recriar Índice HNSW

Se você já tinha um índice IVFFlat, recrie com HNSW:

```bash
python scripts/recreate_hnsw_index.py
```

## 4. Busca na Base de Conhecimento

### Via API

```bash
curl "http://localhost:8000/api/rag/search?query=horários%20de%20atendimento&top_k=5" \
  -H "X-API-Key: sua_chave_aqui"
```

**Resposta:**
```json
{
    "results": [
        {
            "content": "Nossos horários de atendimento são de segunda a sexta...",
            "source": "documento.pdf",
            "document_id": "doc_123",
            "similarity": 0.92,
            "metadata": {
                "original_filename": "documento.pdf",
                "uploaded_at": "2024-01-15T10:30:00"
            }
        }
    ]
}
```

### Via Python

```python
from src.modules.rag.rag_service import RAGService

service = RAGService()

resultados = await service.search(
    query="Quais são os horários de atendimento?",
    top_k=5,
    similarity_threshold=0.7
)

for resultado in resultados:
    print(f"Conteúdo: {resultado['content']}")
    print(f"Similaridade: {resultado['similarity']:.2f}")
    print(f"Fonte: {resultado['source']}")
    print("---")
```

## 5. Uso Automático pelo Agente

Quando o módulo RAG está ativo, o agente usa automaticamente:

```python
# No orchestrator.py
if self.active_modules.get("knowledge"):
    rag_service = RAGService()
    context_documents = await rag_service.search(
        query=user_message,
        top_k=config.rag.top_k
    )
    # Contexto é passado para o LLM junto com a pergunta
```

## Estrutura do Banco de Dados

```sql
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),  -- Vetor de embeddings
    metadata JSONB,          -- Metadados do documento
    source VARCHAR(500),     -- Caminho do arquivo original
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, chunk_index)
);

-- Índice HNSW para busca rápida
CREATE INDEX document_chunks_embedding_idx 
ON document_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

## Exemplo Completo

### 1. Upload

```bash
curl -X POST http://localhost:8000/api/rag/upload \
  -H "X-API-Key: sua_chave" \
  -F "file=@politica_atendimento.pdf"
```

### 2. Buscar

```bash
curl "http://localhost:8000/api/rag/search?query=política%20de%20devolução&top_k=3" \
  -H "X-API-Key: sua_chave"
```

### 3. Usar no Agente

Quando um usuário pergunta "Qual é a política de devolução?", o agente:
1. Busca na base de conhecimento
2. Encontra chunks relevantes
3. Usa o contexto para gerar resposta precisa

## Otimizações

### Ajustar Parâmetros HNSW

Para melhor qualidade (mais lento):
```sql
CREATE INDEX ... WITH (m = 32, ef_construction = 128);
```

Para mais velocidade (qualidade menor):
```sql
CREATE INDEX ... WITH (m = 8, ef_construction = 32);
```

### Ajustar ef_search (em runtime)

Para buscas mais precisas:
```python
# No código de busca, você pode ajustar ef_search
# (atualmente usa o padrão do PostgreSQL)
```

## Troubleshooting

### Erro: "index does not exist"

Execute:
```bash
python scripts/recreate_hnsw_index.py
```

### Buscas muito lentas

1. Verifique se o índice HNSW existe
2. Considere reduzir `top_k`
3. Ajuste `similarity_threshold`

### Resultados não relevantes

1. Ajuste `similarity_threshold` (padrão: 0.7)
2. Verifique qualidade dos documentos
3. Considere chunks menores (`RAG_CHUNK_SIZE`)

