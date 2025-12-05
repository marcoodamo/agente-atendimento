# Interface Gráfica

A interface gráfica permite interagir com o sistema de forma visual e intuitiva.

## 🚀 Início Rápido

### Instalação

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate

# 2. Instalar Streamlit (se necessário)
python -m pip install streamlit requests

# Ou instalar todas as dependências
python -m pip install -r requirements.txt
```

### Iniciar Interface

**Opção 1: Docker Compose (Recomendado)**
```bash
./start.sh
```

A interface estará disponível em: **http://localhost:30001**

**Opção 2: Manual (sem Docker)**
```bash
source venv/bin/activate
streamlit run interface.py --server.port 8501
```

A interface estará disponível em: **http://localhost:8501**

## ⚙️ Configuração

Na sidebar da interface você pode configurar:
- **API URL**: Padrão `http://localhost:8000`
- **API Key**: Sua chave de autenticação (do arquivo `.env`)

## Funcionalidades

### 1. 💬 Conversar

Interface de chat para conversar diretamente com o agente:

- **Histórico de conversa**: Mantém contexto da conversa
- **Fontes**: Mostra documentos utilizados nas respostas
- **Detalhes**: Exibe metadados completos das respostas
- **Limpar**: Botão para reiniciar a conversa

**Como usar:**
1. Digite sua mensagem no campo de input
2. Pressione Enter ou clique em enviar
3. Veja a resposta do agente
4. Explore as fontes e detalhes se necessário

### 2. 📄 Base de Conhecimento

Upload e gerenciamento de documentos:

- **Upload de arquivos**: PDF, DOCX, TXT
- **ID customizado**: Opcional, gera automaticamente se não fornecido
- **Processamento automático**: Chunks, embeddings e indexação

**Como usar:**
1. Clique em "Browse files" ou arraste um arquivo
2. (Opcional) Digite um ID para o documento
3. Clique em "Fazer Upload"
4. Aguarde o processamento

### 3. 🔍 Testar RAG

Teste de busca na base de conhecimento:

- **Query de busca**: Digite sua pergunta
- **Top K**: Ajuste número de resultados
- **Exemplos**: Queries pré-definidas para teste
- **Resultados detalhados**: Similaridade, conteúdo, metadados

**Como usar:**
1. Digite uma query ou selecione um exemplo
2. Ajuste o número de resultados (Top K)
3. Clique em "Buscar"
4. Explore os resultados e similaridades

### 4. 🧪 Testes do Sistema

Suite completa de testes:

#### 🔌 Conectividade
- Health Check
- Info do Serviço
- Autenticação

#### 💬 Processamento de Mensagens
- Mensagens pré-definidas
- Mensagens customizadas
- Métricas de performance

#### 📚 RAG (Base de Conhecimento)
- Upload de documentos
- Busca simples
- Busca com múltiplos resultados

#### 🔍 Busca Vetorial
- Teste múltiplas queries
- Comparação de resultados
- Análise de similaridade

#### ⚙️ Configuração
- Verificar configurações
- Status dos endpoints
- Validação de autenticação

#### 🔄 Integração Completa
- Fluxo completo end-to-end
- Upload → Busca → Processamento
- Validação de integração

## Configurações

### Sidebar

Na barra lateral você pode:

- **API URL**: Configurar URL da API (padrão: http://localhost:8000)
- **API Key**: Configurar chave de autenticação
- **Status**: Ver status da conexão com a API

## Exemplos de Uso

### Teste Completo de RAG

1. Vá para "📄 Base de Conhecimento"
2. Faça upload de um documento PDF
3. Vá para "🔍 Testar RAG"
4. Digite uma query relacionada ao documento
5. Veja os resultados com similaridade

### Teste de Conversação

1. Vá para "💬 Conversar"
2. Digite: "Olá, como você está?"
3. Veja a resposta do agente
4. Continue a conversa
5. Explore as fontes utilizadas

### Teste de Performance

1. Vá para "🧪 Testes do Sistema"
2. Selecione "💬 Processamento de Mensagens"
3. Execute múltiplos testes
4. Analise os tempos de resposta
5. Compare diferentes tipos de mensagens

## Troubleshooting

### Interface não inicia

```bash
# Verificar se Streamlit está instalado
pip install streamlit requests

# Verificar porta
# A porta 8501 pode estar em uso, mude no script
```

### Erro de conexão com API

1. Verifique se a API está rodando: `curl http://localhost:8000/health`
2. Verifique a URL na sidebar
3. Verifique a API Key

### Upload não funciona

1. Verifique formato do arquivo (PDF, DOCX, TXT)
2. Verifique tamanho do arquivo
3. Veja logs do servidor da API

## Recursos Adicionais

- **Atualização em tempo real**: Interface atualiza automaticamente
- **Histórico persistente**: Conversas mantidas durante a sessão
- **Export de resultados**: Copie JSONs para análise
- **Múltiplas abas**: Navegue entre funcionalidades facilmente

## Próximos Passos

Após usar a interface:

1. Analise os resultados dos testes
2. Ajuste configurações conforme necessário
3. Use os dados para melhorar o sistema
4. Documente problemas encontrados

