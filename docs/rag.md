# RAG - Base de Conhecimento Vetorial

O módulo RAG (Retrieval-Augmented Generation) permite que o agente responda perguntas usando informações da base de conhecimento da empresa.

## Visão Geral

O RAG funciona em três etapas:

1. **Indexação**: Documentos são processados e convertidos em embeddings vetoriais
2. **Busca**: Perguntas do usuário são convertidas em embeddings e comparadas com documentos
3. **Geração**: O contexto encontrado é usado pelo LLM para gerar respostas precisas

## Configuração

### Habilitar Módulo

```env
ENABLE_KNOWLEDGE=true
```

### Configurações RAG

```env
# Embeddings
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# Busca
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.3  # Reduzido para melhor recall (padrão era 0.7)
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
```

## 🚀 Início Rápido

### Habilitar RAG

1. **Iniciar Docker Desktop** (necessário para PostgreSQL com pgvector)
2. **Iniciar serviços**:
   ```bash
   docker-compose up -d
   ```
3. **Criar banco de dados** (primeira vez):
   ```bash
   python scripts/create_db.py
   python scripts/init_db.py
   ```
4. **Iniciar API com RAG habilitado**:
   ```bash
   export ENABLE_KNOWLEDGE=true
   export POSTGRES_PORT=5433
   python -m src.main --mode api --port 8000
   ```

### Troubleshooting

**Erro: "extension vector is not available"**
- Docker não está rodando → Inicie Docker Desktop
- PostgreSQL local sem pgvector → Use Docker (porta 5433)

**Erro: "Módulo RAG está desabilitado"**
- Exporte `ENABLE_KNOWLEDGE=true` antes de iniciar a API

**Upload não funciona**
- Verifique se Docker está rodando: `docker ps`
- Verifique se containers estão up: `docker-compose ps`
- Verifique logs: `docker-compose logs postgres`

## Adicionar Documentos

### Via Interface Web (Recomendado)

1. Acesse http://localhost:8501
2. Vá para aba "📄 Base de Conhecimento"
3. Selecione arquivo (PDF, DOCX, TXT)
4. Clique em "Fazer Upload"

### Via Script

```bash
python scripts/add_document.py /caminho/para/documento.pdf
```

### Via API

```bash
curl -X POST http://localhost:8000/api/rag/upload \
  -H "X-API-Key: sua_chave" \
  -F "file=@documento.pdf" \
  -F "document_id=doc_123"
```

**Ou via add-document endpoint:**

```bash
curl -X POST http://localhost:8000/api/rag/add-document \
  -H "X-API-Key: sua_chave" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/caminho/para/documento.pdf",
    "document_id": "doc_123"
  }'
```

### Via Código

```python
from src.modules.rag.rag_service import RAGService

service = RAGService()

doc_id = await service.add_document(
    file_path="/caminho/para/documento.pdf",
    document_id="doc_123"  # Opcional
)
```

## Formatos Suportados

- **PDF** (`.pdf`)
- **Word** (`.docx`)
- **Texto** (`.txt`)

## Buscar na Base de Conhecimento

### Via API

```bash
curl "http://localhost:8000/api/rag/search?query=horários%20de%20atendimento&top_k=5" \
  -H "X-API-Key: sua_chave"
```

### Via Código

```python
from src.modules.rag.rag_service import RAGService

service = RAGService()

resultados = await service.search(
    query="Quais são os horários de atendimento?",
    top_k=5
)

for resultado in resultados:
    print(f"Conteúdo: {resultado['content']}")
    print(f"Fonte: {resultado['source']}")
    print(f"Score: {resultado['score']}")
```

## Como Funciona

### 1. Processamento de Documentos

```python
from src.modules.rag.document_processor import DocumentProcessor

processor = DocumentProcessor()

# Processar documento
chunks = await processor.process_document(
    file_path="documento.pdf",
    chunk_size=1000,
    chunk_overlap=200
)

# Chunks são pedaços do documento de tamanho similar
for chunk in chunks:
    print(chunk.text)
    print(chunk.metadata)
```

### 2. Geração de Embeddings

```python
from src.modules.rag.embedding_service import EmbeddingService

embedding_service = EmbeddingService()

# Gerar embedding de um texto
embedding = await embedding_service.generate_embedding(
    text="Este é um texto de exemplo"
)

# Embedding é um vetor numérico (ex: 1536 dimensões)
print(f"Dimensões: {len(embedding)}")
```

### 3. Armazenamento Vetorial

Os embeddings são armazenados no PostgreSQL com PGVector:

```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id VARCHAR(255),
    content TEXT,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP
);

CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

### 4. Busca por Similaridade

```python
# A busca compara o embedding da query com os embeddings dos documentos
query_embedding = await embedding_service.generate_embedding(query)

# Busca vetorial usando cosine similarity
results = await service._vector_search(query_embedding, top_k=5)
```

## Uso Automático pelo Agente

Quando o módulo RAG está ativo, o agente usa automaticamente a base de conhecimento:

```python
# No orchestrator.py
if self.active_modules.get("knowledge"):
    rag_service = RAGService()
    context_documents = await rag_service.search(
        query=user_message,
        top_k=config.rag.top_k
    )
    # Contexto é passado para o LLM
```

## Otimização

### Ajustar Chunk Size

Chunks menores = mais precisos, mas mais chunks
Chunks maiores = menos precisos, mas menos chunks

```env
RAG_CHUNK_SIZE=500   # Chunks menores
RAG_CHUNK_SIZE=2000  # Chunks maiores
```

### Ajustar Similarity Threshold

```env
RAG_SIMILARITY_THRESHOLD=0.8  # Mais restritivo
RAG_SIMILARITY_THRESHOLD=0.5  # Menos restritivo
```

### Ajustar Top K

```env
RAG_TOP_K=3   # Menos resultados, mais rápidos
RAG_TOP_K=10  # Mais resultados, mais contexto
```

## Provedores de Embeddings

### OpenAI (Padrão)

```env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
```

**Vantagens:**
- Alta qualidade
- Fácil de usar
- Suporte a múltiplos idiomas

**Desvantagens:**
- Custo por requisição
- Requer conexão com internet

### Sentence Transformers (Local)

```env
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
```

**Vantagens:**
- Gratuito
- Funciona offline
- Rápido

**Desvantagens:**
- Requer mais memória
- Qualidade pode ser inferior

## Manutenção

### Atualizar Documentos

Para atualizar um documento, adicione novamente com o mesmo `document_id`:

```python
await service.add_document(
    file_path="documento_atualizado.pdf",
    document_id="doc_123"  # Mesmo ID
)
```

### Listar Documentos

**Via Interface Web:**
1. Acesse http://localhost:8501
2. Vá para aba "📄 Base de Conhecimento"
3. Role até "📋 Gerenciar Documentos"
4. Clique em "🔄 Atualizar Lista"

**Via API:**
```bash
curl "http://localhost:8000/api/rag/documents" \
  -H "X-API-Key: sua_chave"
```

**Via Código:**
```python
from src.modules.rag.rag_service import RAGService

service = RAGService()
documents = await service.list_documents()

for doc in documents:
    print(f"ID: {doc['document_id']}")
    print(f"Arquivo: {doc['filename']}")
    print(f"Chunks: {doc['chunk_count']}")
```

### Excluir Documentos

**Via Interface Web:**
1. Na seção "📋 Gerenciar Documentos"
2. Selecione o documento no dropdown
3. Clique em "🗑️ Excluir Documento"

**Via API:**
```bash
curl -X DELETE "http://localhost:8000/api/rag/documents/{document_id}" \
  -H "X-API-Key: sua_chave"
```

**Via Código:**
```python
from src.modules.rag.rag_service import RAGService

service = RAGService()
# Remover todos os chunks de um documento
success = await service.delete_document(document_id="doc_123")
```

### Limpar Base de Conhecimento

```sql
-- Cuidado: Remove todos os documentos!
TRUNCATE TABLE document_chunks;
```

## Boas Práticas

1. **Organize documentos**: Use `document_id` descritivos
2. **Atualize regularmente**: Mantenha informações atualizadas
3. **Teste queries**: Verifique se as buscas retornam resultados relevantes
4. **Monitore qualidade**: Ajuste thresholds conforme necessário
5. **Use metadados**: Adicione tags e categorias nos metadados

## Exemplo Completo

```python
from src.modules.rag.rag_service import RAGService

service = RAGService()

# 1. Adicionar documentos
doc1_id = await service.add_document(
    file_path="politica_atendimento.pdf",
    document_id="politica_001"
)

doc2_id = await service.add_document(
    file_path="faq.pdf",
    document_id="faq_001"
)

# 2. Buscar informações
resultados = await service.search(
    query="Como funciona o processo de devolução?",
    top_k=5
)

# 3. Usar resultados no agente
contexto = "\n\n".join([
    f"[{i+1}] {r['content']}\nFonte: {r['source']}"
    for i, r in enumerate(resultados)
])

# Contexto é passado para o LLM junto com a pergunta do usuário
```

## Troubleshooting

### Erro: "extension vector is not available"

Certifique-se de que o PostgreSQL tem a extensão pgvector instalada:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Resultados não relevantes

- Ajuste `RAG_SIMILARITY_THRESHOLD`
- Verifique qualidade dos documentos
- Considere usar chunks menores

### Performance lenta

- Reduza `RAG_TOP_K`
- Use índice ivfflat no PostgreSQL
- Considere cache de embeddings

