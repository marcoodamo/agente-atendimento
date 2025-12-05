# Documentação do Agente IA Multicanal

Bem-vindo à documentação completa do sistema de atendimento automatizado.

## 📚 Índice

### 🚀 Início Rápido

- **[Instalação](instalacao.md)** - Guia completo de instalação, comandos rápidos e troubleshooting
- **[Interface Web](interface.md)** - Como usar a interface gráfica Streamlit

### 🏗️ Fundamentos

- **[Arquitetura](arquitetura.md)** - Como o sistema funciona internamente
- **[APIs](apis.md)** - Documentação completa da API REST

### 🔌 Integrações

- **[Integrações](integracoes.md)** - Como integrar com WhatsApp, Calendly, Voz e outros serviços
- **[Follow-up](follow-up.md)** - Sistema de follow-up automático e reengajamento
- **[Voz](voz.md)** - Atendimento por voz (Speech-to-Text e Text-to-Speech)

### 📚 Base de Conhecimento

- **[RAG](rag.md)** - Base de conhecimento vetorial, upload, busca e gerenciamento de documentos
- **[RAG - Fluxo Detalhado](rag-fluxo.md)** - Fluxo completo de funcionamento do RAG

### 🛠️ Customização

- **[Edição e Customização](edicao.md)** - Como editar, customizar e estender o sistema

### 🚀 Deploy e Segurança

- **[Deploy com Docker](deploy.md)** - Guia completo de deploy usando Docker Compose
- **[Segurança](seguranca.md)** - Medidas de segurança e configuração para produção

## 🚀 Início Rápido

1. **Instale o sistema**: Siga o [Guia de Instalação](instalacao.md)
2. **Inicie os serviços**: Use `./start.sh` (Docker Compose recomendado)
3. **Acesse a interface**: http://localhost:8501
4. **Configure integrações**: Veja [Integrações](integracoes.md) para WhatsApp, Calendly, etc.
5. **Adicione conhecimento**: Use a [Interface Web](interface.md) para fazer upload de documentos
6. **Customize**: Consulte [Edição](edicao.md) para personalizar o sistema

## 📖 Estrutura da Documentação

Cada documento contém:
- Visão geral do módulo/funcionalidade
- Configuração passo a passo
- Exemplos de código
- Troubleshooting
- Boas práticas

## 🔍 Encontrar o que Precisa

- **Quer instalar?** → [Instalação](instalacao.md)
- **Quer usar a interface?** → [Interface Web](interface.md)
- **Quer adicionar documentos?** → [RAG](rag.md) → Adicionar Documentos
- **Quer gerenciar documentos?** → [RAG](rag.md) → Gerenciar Documentos
- **Quer integrar WhatsApp?** → [Integrações](integracoes.md) → WhatsApp
- **Quer usar a API?** → [APIs](apis.md)
- **Quer entender como funciona?** → [Arquitetura](arquitetura.md)
- **Quer customizar?** → [Edição](edicao.md)

## 💡 Dicas

- Use a busca do seu editor para encontrar termos específicos
- Os exemplos de código são funcionais e podem ser copiados diretamente
- Sempre verifique os logs em caso de problemas

## 📝 Contribuindo

Se encontrar erros ou tiver sugestões de melhoria na documentação, por favor abra uma issue ou pull request.

