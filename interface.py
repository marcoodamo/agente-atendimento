"""
Interface gráfica para o Agente IA Multicanal
Interface web simples usando Streamlit
"""
import streamlit as st
import requests
import json
from pathlib import Path
import os
from typing import Dict, Any, List, Optional
import time
from streamlit.runtime.uploaded_file_manager import UploadedFile

# Configuração da página
st.set_page_config(
    page_title="Agente IA Multicanal",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .test-result {
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Configurações
API_URL = os.getenv("API_URL", "http://localhost:30000")
API_KEY = os.getenv("API_KEY", "d1225caa-66bf-4602-8ced-3a7abfb2cc85")

# Headers para requisições
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def check_api_health() -> bool:
    """Verifica se a API está funcionando"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def send_message(message: str, user_id: str, channel: str = "web", rag_metadata_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Envia mensagem para o agente"""
    try:
        payload = {
            "message": message,
            "user_id": user_id,
            "channel": channel
        }
        if rag_metadata_filter:
            payload["rag_metadata_filter"] = rag_metadata_filter
        
        response = requests.post(
            f"{API_URL}/api/message",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def upload_document(file, document_id: str = None, selected_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Faz upload de documento"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {}
        if document_id:
            data["document_id"] = document_id
        
        # Só enviar selected_metadata se houver valores preenchidos
        if selected_metadata and isinstance(selected_metadata, dict):
            # Filtrar apenas valores não vazios
            filtered_metadata = {k: v for k, v in selected_metadata.items() if v and v != ""}
            if filtered_metadata:
                data["selected_metadata"] = json.dumps(filtered_metadata)
        
        headers = {"X-API-Key": API_KEY}
        
        response = requests.post(
            f"{API_URL}/api/rag/upload",
            headers=headers,
            files=files,
            data=data,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def search_rag(query: str, top_k: int = 5, similarity_threshold: float = 0.1, metadata_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Busca na base de conhecimento RAG"""
    try:
        params = {"query": query, "top_k": top_k, "similarity_threshold": similarity_threshold}
        if metadata_filter:
            params["metadata_filter"] = json.dumps(metadata_filter)
        
        response = requests.get(
            f"{API_URL}/api/rag/search",
            headers={"X-API-Key": API_KEY},
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_metadata_fields() -> List[Dict[str, Any]]:
    """Obtém lista de campos de metadata disponíveis"""
    try:
        # Usar valores atuais de API_URL e API_KEY
        current_api_url = st.session_state.get("current_api_url", API_URL)
        current_api_key = st.session_state.get("current_api_key", API_KEY)
        
        response = requests.get(
            f"{current_api_url}/api/rag/metadata/fields",
            headers={"X-API-Key": current_api_key},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, dict):
                return data.get("fields", [])
        return []
    except Exception:
        # Silenciosamente retorna lista vazia se houver qualquer erro
        return []

def render_metadata_selector(key_prefix: str) -> Optional[Dict[str, Any]]:
    """
    Renderiza interface para seleção de metadata
    Retorna um dicionário com os filtros selecionados ou None
    """
    try:
        metadata_fields = get_metadata_fields()
    except Exception as e:
        # Se houver erro ao buscar campos, retorna None sem quebrar a interface
        return None
    
    if not metadata_fields or len(metadata_fields) == 0:
        return None
    
    st.subheader("🏷️ Filtros de Metadata (Opcional)")
    st.caption("💡 Selecione valores de metadata para filtrar os resultados da busca")
    
    selected_metadata = {}
    
    # Criar campos para cada metadata disponível
    cols_per_row = 2
    for i in range(0, len(metadata_fields), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, field in enumerate(metadata_fields[i:i+cols_per_row]):
            if not field or not isinstance(field, dict) or "field_key" not in field:
                continue
                
            with cols[j]:
                try:
                    field_key = field["field_key"]
                    field_label = field.get("field_label", field_key)
                    field_type = field.get("field_type", "text")
                    field_options = field.get("field_options", {}).get("options", []) if field.get("field_type") == "select" else None
                    
                    st.write(f"**{field_label}**")
                    
                    if field_type == "select" and field_options:
                        value = st.selectbox(
                            "Valor",
                            options=[""] + field_options,
                            key=f"{key_prefix}_metadata_{field_key}",
                            label_visibility="collapsed",
                            help=f"Selecione um valor para {field_label} (deixe em branco para não filtrar)"
                        )
                        if value:
                            selected_metadata[field_key] = value
                    else:
                        value = st.text_input(
                            "Valor",
                            key=f"{key_prefix}_metadata_{field_key}",
                            label_visibility="collapsed",
                            placeholder="Deixe em branco para não filtrar",
                            help=f"Digite um valor para {field_label}"
                        )
                        if value:
                            selected_metadata[field_key] = value
                except Exception as e:
                    # Ignorar erros em campos individuais
                    continue
    
    return selected_metadata if selected_metadata else None

# Sidebar
with st.sidebar:
    st.title("⚙️ Configurações")
    
    # Inicializar session_state se necessário
    if "current_api_url" not in st.session_state:
        st.session_state.current_api_url = API_URL
    if "current_api_key" not in st.session_state:
        st.session_state.current_api_key = API_KEY
    
    api_url_input = st.text_input("API URL", value=st.session_state.current_api_url)
    api_key_input = st.text_input("API Key", value=st.session_state.current_api_key, type="password")
    
    if api_url_input != st.session_state.current_api_url or api_key_input != st.session_state.current_api_key:
        st.session_state.current_api_url = api_url_input
        st.session_state.current_api_key = api_key_input
        API_URL = api_url_input
        API_KEY = api_key_input
        HEADERS["X-API-Key"] = API_KEY
        st.rerun()
    
    st.divider()
    
    # Status da API
    st.subheader("📊 Status")
    if check_api_health():
        st.success("✅ API Online")
    else:
        st.error("❌ API Offline")
        st.info("Certifique-se de que o servidor está rodando em " + API_URL)

# Título principal
st.markdown('<div class="main-header">🤖 Agente IA Multicanal</div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Conversar", 
    "📄 Base de Conhecimento", 
    "🔍 Testar RAG", 
    "🧪 Testes do Sistema"
])

# TAB 1: Conversar com o Agente
with tab1:
    st.header("💬 Conversar com o Agente")
    
    # Inicializar histórico de conversa
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Seleção de metadata para filtro RAG
    try:
        rag_metadata_filter = render_metadata_selector("chat")
    except Exception as e:
        # Se houver erro, continua sem filtro de metadata
        rag_metadata_filter = None
    
    # Mostrar histórico
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "sources" in msg and msg["sources"]:
                with st.expander("📚 Fontes"):
                    for source in msg["sources"]:
                        st.write(f"- {source}")
    
    # Input do usuário
    user_input = st.chat_input("Digite sua mensagem...")
    
    if user_input:
        # Adicionar mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        
        # Processar com o agente
        with st.chat_message("assistant"):
            with st.spinner("Processando..."):
                result = send_message(user_input, "web_user", "web", rag_metadata_filter=rag_metadata_filter)
            
            if "error" in result:
                st.error(f"Erro: {result['error']}")
            else:
                response = result.get("response", "Sem resposta")
                st.write(response)
                
                # Mostrar fontes se houver
                sources = result.get("sources", [])
                if sources:
                    with st.expander("📚 Fontes utilizadas"):
                        for source in sources:
                            st.write(f"- {source}")
                
                # Mostrar metadados
                with st.expander("🔍 Detalhes"):
                    st.json(result)
                
                # Adicionar ao histórico
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "sources": sources
                })
    
    # Botão para limpar histórico
    if st.button("🗑️ Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()

# TAB 2: Base de Conhecimento (Upload)
with tab2:
    st.header("📄 Gerenciar Base de Conhecimento")
    
    # Tabs dentro da tab de Base de Conhecimento
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📤 Upload", "🏷️ Metadata", "📋 Documentos"])
    
    with sub_tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📤 Upload de Documento")
        
        uploaded_file = st.file_uploader(
            "Selecione um arquivo",
            type=["pdf", "docx", "txt"],
            help="Formatos suportados: PDF, DOCX, TXT"
        )
        
        document_id = st.text_input(
            "ID do Documento (opcional)",
            help="Deixe em branco para gerar automaticamente"
        )
        
        # Carregar campos de metadata disponíveis
        metadata_fields = {}
        try:
            response = requests.get(
                f"{API_URL}/api/rag/metadata/fields",
                headers={"X-API-Key": API_KEY},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                fields = data.get("fields", [])
                for field in fields:
                    metadata_fields[field["field_key"]] = field
        except:
            pass
        
        # Seleção de metadata - Interface dinâmica
        st.subheader("🏷️ Metadata (Opcional)")
        st.caption("💡 Adicione campos de metadata ao documento. Você pode adicionar múltiplos campos.")
        
        # Inicializar session_state para metadata do upload
        if "upload_metadata_fields" not in st.session_state:
            st.session_state.upload_metadata_fields = []
        
        # Lista de campos disponíveis para adicionar
        available_fields_list = []
        if metadata_fields:
            for field_key, field in metadata_fields.items():
                available_fields_list.append({
                    "key": field_key,
                    "label": field.get("field_label", field_key),
                    "type": field.get("field_type", "text"),
                    "options": field.get("field_options", {}).get("options", []) if field.get("field_type") == "select" else None
                })
        
        # Mostrar campos já adicionados
        if st.session_state.upload_metadata_fields:
            st.write("**Campos adicionados:**")
            for idx, field_info in enumerate(st.session_state.upload_metadata_fields):
                field_key = field_info["field_key"]
                field_label = field_info["field_label"]
                field_type = field_info["field_type"]
                field_options = field_info.get("options")
                
                col_field, col_remove = st.columns([4, 1])
                
                with col_field:
                    if field_type == "select" and field_options:
                        value = st.selectbox(
                            field_label,
                            options=[""] + field_options,
                            key=f"upload_metadata_value_{field_key}_{idx}",
                            help=f"Selecione um valor para {field_label}"
                        )
                    else:
                        value = st.text_input(
                            field_label,
                            key=f"upload_metadata_value_{field_key}_{idx}",
                            help=f"Digite um valor para {field_label} (deixe em branco para null)",
                            placeholder="Digite o valor..."
                        )
                    
                    # Armazenar valor
                    if value:
                        field_info["value"] = value
                    else:
                        field_info["value"] = None
                
                with col_remove:
                    st.write("")  # Espaço
                    st.write("")  # Espaço
                    if st.button("🗑️", key=f"remove_metadata_{idx}", help="Remover campo"):
                        st.session_state.upload_metadata_fields.pop(idx)
                        st.rerun()
        
        # Adicionar novo campo
        if available_fields_list:
            st.divider()
            st.write("**➕ Adicionar campo de metadata:**")
            
            # Filtrar campos já adicionados
            added_field_keys = {f["field_key"] for f in st.session_state.upload_metadata_fields}
            available_to_add = [f for f in available_fields_list if f["key"] not in added_field_keys]
            
            if available_to_add:
                col_select, col_add = st.columns([3, 1])
                
                with col_select:
                    selected_field_key = st.selectbox(
                        "Selecione um campo para adicionar:",
                        options=[""] + [f"{f['label']} ({f['key']})" for f in available_to_add],
                        key="select_metadata_field",
                        help="Escolha um campo de metadata para adicionar"
                    )
                
                with col_add:
                    st.write("")  # Espaço
                    st.write("")  # Espaço
                    if st.button("➕ Adicionar", key="add_metadata_field", use_container_width=True):
                        if selected_field_key:
                            # Extrair field_key do formato "Label (key)"
                            selected_field = None
                            for f in available_to_add:
                                if f"{f['label']} ({f['key']})" == selected_field_key:
                                    selected_field = f
                                    break
                            
                            if selected_field:
                                st.session_state.upload_metadata_fields.append({
                                    "field_key": selected_field["key"],
                                    "field_label": selected_field["label"],
                                    "field_type": selected_field["type"],
                                    "options": selected_field["options"],
                                    "value": None
                                })
                                st.rerun()
            else:
                st.info("✅ Todos os campos disponíveis já foram adicionados")
        else:
            st.info("📭 Nenhum campo de metadata configurado. Crie campos na aba '🏷️ Metadata' primeiro.")
        
        # Preparar selected_metadata para envio
        selected_metadata = {}
        for field_info in st.session_state.upload_metadata_fields:
            if field_info.get("value"):
                selected_metadata[field_info["field_key"]] = field_info["value"]
        
        if st.button("⬆️ Fazer Upload", type="primary"):
            if uploaded_file:
                with st.spinner("Processando documento..."):
                    result = upload_document(
                        uploaded_file, 
                        document_id if document_id else None,
                        selected_metadata if selected_metadata else None
                    )
                
                if "error" in result:
                    error_msg = result['error']
                    # Mensagens de erro mais amigáveis
                    if "Módulo RAG está desabilitado" in error_msg or "503" in str(result):
                        st.error("❌ **Módulo RAG Desabilitado**")
                        st.warning("""
                        Para fazer upload de documentos, você precisa:
                        1. Iniciar Docker Desktop
                        2. Executar: `docker-compose up -d`
                        3. Reiniciar a API com módulo RAG habilitado
                        
                        Ou use o script: `./start.sh`
                        """)
                    elif "vector" in error_msg.lower() or "extension" in error_msg.lower() or "pgvector" in error_msg.lower():
                        st.error("❌ **Erro de Banco de Dados**")
                        st.warning("""
                        PostgreSQL com pgvector não está disponível.
                        
                        Solução:
                        1. Inicie Docker Desktop
                        2. Execute: `docker-compose up -d`
                        3. Aguarde alguns segundos
                        4. Tente novamente
                        """)
                    elif "500" in str(error_msg) or "Internal Server Error" in error_msg:
                        st.error("❌ **Erro no Servidor (500)**")
                        st.warning("""
                        O servidor encontrou um erro ao processar o upload.
                        
                        Possíveis causas:
                        1. Banco de dados não está acessível
                        2. Erro ao processar o documento
                        3. Problema de conexão
                        
                        Verifique os logs do servidor para mais detalhes.
                        """)
                        with st.expander("🔍 Detalhes do Erro"):
                            st.code(error_msg, language="text")
                    else:
                        st.error(f"❌ Erro: {error_msg}")
                else:
                    st.success(f"✅ Documento adicionado com sucesso!")
                    st.info(f"**ID do Documento:** {result.get('document_id')}")
                    # Limpar metadata do upload após sucesso
                    st.session_state.upload_metadata_fields = []
                    st.rerun()
            else:
                st.warning("⚠️ Selecione um arquivo primeiro")
    
    with col2:
        st.subheader("ℹ️ Informações")
        st.info("""
        **Formatos Suportados:**
        - PDF (.pdf)
        - Word (.docx)
        - Texto (.txt)
        
        **Processamento:**
        - Documentos são divididos em chunks
        - Cada chunk vira um embedding vetorial
        - Armazenado com índice HNSW
        """)
        
        st.divider()
        
        st.subheader("📋 Gerenciar Documentos")
        if st.button("🔄 Atualizar Lista", use_container_width=True, key="refresh_upload_docs"):
            st.rerun()
    
    with sub_tab2:
        st.header("🏷️ Gerenciar Metadata")
        
        # Primeiro: Seleção obrigatória de documento
        st.subheader("📄 Passo 1: Selecionar Documento")
        
        # Carregar lista de documentos
        documents_list = []
        try:
            response = requests.get(
                f"{API_URL}/api/rag/documents",
                headers={"X-API-Key": API_KEY},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                documents_list = data.get("documents", [])
        except:
            pass
        
        if not documents_list:
            st.warning("⚠️ Nenhum documento encontrado. Faça upload de um documento primeiro na aba 'Upload'.")
        else:
            # Criar opções para selectbox
            doc_options = {}
            for doc in documents_list:
                filename = doc.get("filename", "N/A")
                doc_id = doc.get("document_id", "")
                chunk_count = doc.get("chunk_count", 0)
                label = f"{filename} ({chunk_count} chunks) - {doc_id[:8]}..."
                doc_options[label] = doc
            
            selected_doc_label = st.selectbox(
                "🔍 Selecione o documento para gerenciar metadata:",
                options=list(doc_options.keys()),
                key="metadata_doc_selector",
                help="Selecione o documento que deseja gerenciar"
            )
            
            if selected_doc_label:
                selected_doc = doc_options[selected_doc_label]
                selected_doc_id = selected_doc["document_id"]
                
                # Mostrar informações do documento selecionado
                st.info(f"""
                **📄 Documento Selecionado:**
                - **Arquivo:** {selected_doc.get('filename', 'N/A')}
                - **ID:** `{selected_doc_id}`
                - **Chunks:** {selected_doc.get('chunk_count', 0)}
                """)
                
                st.divider()
                
                # Segundo: Gerenciar campos de metadata (criar/editar/excluir)
                st.subheader("🔧 Passo 2: Gerenciar Campos de Metadata")
                st.caption("💡 **Campos de metadata** são como 'categorias' que você pode criar (ex: 'departamento', 'categoria'). Cada campo pode ter um **valor** diferente em cada documento ou chunk.")
                
                col_fields, col_create = st.columns([2, 1])
                
                with col_fields:
                    st.write("**📋 Campos Disponíveis:**")
                    
                    # Listar campos
                    try:
                        fields_response = requests.get(
                            f"{API_URL}/api/rag/metadata/fields",
                            headers={"X-API-Key": API_KEY},
                            timeout=10
                        )
                        if fields_response.status_code == 200:
                            fields_data = fields_response.json()
                            if fields_data is None:
                                fields_data = {}
                            fields = fields_data.get("fields", []) if fields_data else []
                            total_fields = fields_data.get("total", 0) if fields_data else 0
                            
                            if total_fields > 0:
                                for field in fields:
                                    if field and isinstance(field, dict) and "field_key" in field:
                                        with st.container():
                                            col_label, col_type, col_action = st.columns([3, 2, 1])
                                            with col_label:
                                                field_name = field.get('field_label', field.get('field_key', 'N/A'))
                                                field_key = field.get('field_key', 'N/A')
                                                st.write(f"**{field_name}**")
                                                st.caption(f"ID: `{field_key}`")
                                            with col_type:
                                                st.write(f"Tipo: {field.get('field_type', 'text')}")
                                                if field.get('field_options') and isinstance(field.get('field_options'), dict):
                                                    options = field.get('field_options', {}).get('options', [])
                                                    if options:
                                                        options_preview = ', '.join(options[:3])
                                                        if len(options) > 3:
                                                            options_preview += "..."
                                                        st.caption(f"Opções: {options_preview}")
                                            with col_action:
                                                st.write("")  # Espaço
                                                if st.button("🗑️ Excluir", key=f"del_field_{field_key}", type="secondary", use_container_width=True):
                                                    try:
                                                        with st.spinner("Excluindo campo..."):
                                                            delete_response = requests.delete(
                                                                f"{API_URL}/api/rag/metadata/fields/{field_key}",
                                                                headers={"X-API-Key": API_KEY},
                                                                timeout=10
                                                            )
                                                            delete_response.raise_for_status()
                                                            st.success(f"✅ Campo '{field_name}' excluído!")
                                                            st.rerun()
                                                    except Exception as e:
                                                        st.error(f"❌ Erro ao excluir: {str(e)}")
                                        st.divider()
                            else:
                                st.info("📭 Nenhum campo criado ainda. Crie um campo ao lado.")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Erro de conexão ao carregar campos: {str(e)}")
                    except Exception as e:
                        st.error(f"❌ Erro ao carregar campos: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                
                with col_create:
                    st.write("**➕ Criar Novo Campo:**")
                    
                    with st.form("create_metadata_field", clear_on_submit=True):
                        field_name = st.text_input(
                            "🏷️ Nome do Campo",
                            placeholder="departamento",
                            help="Será usado como nome e ID (sem espaços, minúsculas, sem caracteres especiais)"
                        )
                        field_type = st.selectbox(
                            "📝 Tipo",
                            ["text", "number", "select", "date"]
                        )
                        
                        field_options = None
                        if field_type == "select":
                            options_str = st.text_area(
                                "📋 Opções (uma por linha)",
                                placeholder="TI\nVendas\nSuporte"
                            )
                            if options_str:
                                options = [opt.strip() for opt in options_str.split("\n") if opt.strip()]
                                if options:
                                    field_options = {"options": options}
                        
                        submitted = st.form_submit_button("➕ Criar", type="primary", use_container_width=True)
                        
                        if submitted:
                            if field_name:
                                # Normalizar: remover espaços, converter para minúsculas, remover caracteres especiais
                                field_key = field_name.lower().strip().replace(" ", "_")
                                # Remover caracteres especiais (manter apenas letras, números e underscore)
                                import re
                                field_key = re.sub(r'[^a-z0-9_]', '', field_key)
                                
                                if not field_key:
                                    st.warning("⚠️ Nome inválido. Use apenas letras, números e underscore.")
                                else:
                                    try:
                                        create_data = {
                                            "field_key": field_key,
                                            "field_label": field_name,  # Usar o mesmo valor para label
                                            "field_type": field_type
                                        }
                                        if field_options:
                                            create_data["field_options"] = field_options
                                        
                                        create_response = requests.post(
                                            f"{API_URL}/api/rag/metadata/fields",
                                            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                                            json=create_data,
                                            timeout=10
                                        )
                                        create_response.raise_for_status()
                                        st.success(f"✅ Campo '{field_name}' criado!")
                                        st.info(f"💡 Chave gerada: `{field_key}`")
                                        st.rerun()
                                    except Exception as e:
                                        error_msg = str(e)
                                        if "unique constraint" in error_msg.lower() or "already exists" in error_msg.lower():
                                            st.error(f"❌ Já existe um campo com esse nome. Use outro nome.")
                                        else:
                                            st.error(f"❌ Erro: {error_msg}")
                            else:
                                st.warning("⚠️ Preencha o nome do campo")
                
                st.divider()
                
                # Terceiro: Definir valores de metadata para o documento selecionado
                st.subheader("✏️ Passo 3: Definir Valores de Metadata")
                st.caption(f"💡 Defina os **valores** dos campos de metadata para o documento **{selected_doc.get('filename', 'N/A')}**. Estes valores serão aplicados a **todos os {selected_doc.get('chunk_count', 0)} chunks** do documento.")
                
                # Carregar valores atuais
                current_doc_metadata = {}
                try:
                    chunks_resp = requests.get(
                        f"{API_URL}/api/rag/documents/{selected_doc_id}/chunks",
                        headers={"X-API-Key": API_KEY},
                        timeout=10
                    )
                    if chunks_resp.status_code == 200:
                        chunks_data = chunks_resp.json()
                        chunks = chunks_data.get("chunks", [])
                        if chunks and chunks[0].get("metadata"):
                            current_doc_metadata = chunks[0].get("metadata", {})
                except:
                    pass
                
                # Carregar campos disponíveis
                try:
                    fields_response = requests.get(
                        f"{API_URL}/api/rag/metadata/fields",
                        headers={"X-API-Key": API_KEY},
                        timeout=10
                    )
                    if fields_response.status_code == 200:
                        fields_data = fields_response.json()
                        if fields_data is None:
                            fields_data = {}
                        metadata_fields_list = fields_data.get("fields", []) if fields_data else []
                        
                        if metadata_fields_list:
                            doc_metadata_updates = {}
                            
                            # Criar grid de campos
                            cols_per_row = 2
                            for i in range(0, len(metadata_fields_list), cols_per_row):
                                cols = st.columns(cols_per_row)
                                for j, field in enumerate(metadata_fields_list[i:i+cols_per_row]):
                                    with cols[j]:
                                        field_key = field["field_key"]
                                        field_label = field.get("field_label", field_key)
                                        field_type = field.get("field_type", "text")
                                        current_value = current_doc_metadata.get(field_key, "")
                                        
                                        st.write(f"**{field_label}** (`{field_key}`)")
                                        
                                        if field_type == "select" and field.get("field_options", {}).get("options"):
                                            options = field["field_options"]["options"]
                                            value = st.selectbox(
                                                "Valor",
                                                options=[""] + options,
                                                index=0 if not current_value else (options.index(current_value) + 1 if current_value in options else 0),
                                                key=f"doc_val_{selected_doc_id}_{field_key}",
                                                label_visibility="collapsed"
                                            )
                                            if value:
                                                doc_metadata_updates[field_key] = value
                                        else:
                                            value = st.text_input(
                                                "Valor",
                                                value=current_value if current_value else "",
                                                key=f"doc_val_{selected_doc_id}_{field_key}",
                                                placeholder="Deixe em branco para null",
                                                label_visibility="collapsed"
                                            )
                                            if value:
                                                doc_metadata_updates[field_key] = value
                            
                            if st.button("💾 Salvar Valores em Todos os Chunks", type="primary", use_container_width=True):
                                if doc_metadata_updates:
                                    with st.spinner(f"Atualizando {selected_doc.get('chunk_count', 0)} chunks..."):
                                        try:
                                            update_response = requests.put(
                                                f"{API_URL}/api/rag/documents/{selected_doc_id}/metadata",
                                                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                                                json={"metadata_updates": doc_metadata_updates},
                                                timeout=30
                                            )
                                            update_response.raise_for_status()
                                            st.success(f"✅ Valores atualizados em todos os {selected_doc.get('chunk_count', 0)} chunks!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Erro: {str(e)}")
                                else:
                                    st.warning("⚠️ Preencha pelo menos um valor")
                        else:
                            st.info("📭 Crie campos de metadata primeiro no Passo 2")
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")
                
                st.divider()
                
                # Quarto: Editar valores por chunk individual
                st.subheader("🔍 Passo 4: Editar Valores por Chunk (Opcional)")
                st.caption(f"💡 Edite valores de metadata **individualmente** para cada chunk do documento **{selected_doc.get('filename', 'N/A')}**.")
                
                # Inicializar session_state
                if f"view_chunks_{selected_doc_id}" not in st.session_state:
                    st.session_state[f"view_chunks_{selected_doc_id}"] = False
                
                if st.button("📄 Ver/Editar Chunks Individuais", key=f"toggle_chunks_{selected_doc_id}", use_container_width=True):
                    st.session_state[f"view_chunks_{selected_doc_id}"] = not st.session_state[f"view_chunks_{selected_doc_id}"]
                    st.rerun()
                
                if st.session_state.get(f"view_chunks_{selected_doc_id}", False):
                    try:
                        chunks_response = requests.get(
                            f"{API_URL}/api/rag/documents/{selected_doc_id}/chunks",
                            headers={"X-API-Key": API_KEY},
                            timeout=10
                        )
                        if chunks_response.status_code == 200:
                            chunks_data = chunks_response.json()
                            chunks = chunks_data.get("chunks", [])
                            
                            st.write(f"**📄 {len(chunks)} Chunks encontrados:**")
                            
                            for chunk in chunks:
                                with st.expander(f"📄 Chunk {chunk['chunk_index']} - {chunk.get('content', '')[:50]}..."):
                                    st.write("**Conteúdo completo:**")
                                    st.text_area(
                                        "Conteúdo",
                                        value=chunk.get("content_full", chunk.get("content", "")),
                                        height=150,
                                        disabled=True,
                                        key=f"content_{selected_doc_id}_{chunk['chunk_index']}"
                                    )
                                    
                                    st.write("**Valores de Metadata:**")
                                    chunk_metadata_updates = {}
                                    chunk_current_metadata = chunk.get("metadata", {})
                                    
                                    for field in metadata_fields_list:
                                        field_key = field["field_key"]
                                        field_label = field.get("field_label", field_key)
                                        field_type = field.get("field_type", "text")
                                        current_value = chunk_current_metadata.get(field_key, "")
                                        
                                        col_label, col_input = st.columns([1, 2])
                                        with col_label:
                                            st.write(f"**{field_label}:**")
                                        with col_input:
                                            if field_type == "select" and field.get("field_options", {}).get("options"):
                                                options = field["field_options"]["options"]
                                                value = st.selectbox(
                                                    "Valor",
                                                    options=[""] + options,
                                                    index=0 if not current_value else (options.index(current_value) + 1 if current_value in options else 0),
                                                    key=f"chunk_val_{selected_doc_id}_{chunk['chunk_index']}_{field_key}",
                                                    label_visibility="collapsed"
                                                )
                                                if value:
                                                    chunk_metadata_updates[field_key] = value
                                            else:
                                                value = st.text_input(
                                                    "Valor",
                                                    value=current_value if current_value else "",
                                                    key=f"chunk_val_{selected_doc_id}_{chunk['chunk_index']}_{field_key}",
                                                    placeholder="Deixe em branco para null",
                                                    label_visibility="collapsed"
                                                )
                                                if value:
                                                    chunk_metadata_updates[field_key] = value
                                    
                                    if st.button("💾 Salvar Valores deste Chunk", key=f"save_chunk_{selected_doc_id}_{chunk['chunk_index']}", type="primary"):
                                        if chunk_metadata_updates:
                                            with st.spinner("Atualizando..."):
                                                try:
                                                    chunk_update_response = requests.put(
                                                        f"{API_URL}/api/rag/documents/{selected_doc_id}/chunks/{chunk['chunk_index']}/metadata",
                                                        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                                                        json={"metadata_updates": chunk_metadata_updates},
                                                        timeout=30
                                                    )
                                                    chunk_update_response.raise_for_status()
                                                    st.success(f"✅ Valores do Chunk {chunk['chunk_index']} atualizados!")
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"❌ Erro: {str(e)}")
                                        else:
                                            st.warning("⚠️ Nenhum valor para salvar")
                    except Exception as e:
                        st.error(f"❌ Erro ao carregar chunks: {str(e)}")
    
    with sub_tab3:
        st.header("📋 Lista de Documentos")
        
        if st.button("🔄 Atualizar Lista", use_container_width=True, key="refresh_docs_list"):
            st.rerun()
        
        # Listar documentos
        try:
            response = requests.get(
                f"{API_URL}/api/rag/documents",
                headers={"X-API-Key": API_KEY},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                documents = data.get("documents", [])
                total = data.get("total", 0)
                
                if total > 0:
                    st.success(f"📚 {total} documento(s) na base")
                    
                    for doc in documents:
                        with st.container():
                            col_info, col_action = st.columns([4, 1])
                            
                            with col_info:
                                st.write(f"**📄 {doc.get('filename', 'N/A')}**")
                                st.caption(f"ID: `{doc.get('document_id', 'N/A')}` | Chunks: {doc.get('chunk_count', 0)}")
                                if doc.get('created_at'):
                                    st.caption(f"Criado em: {doc['created_at'][:19]}")
                            
                            with col_action:
                                if st.button("🗑️ Excluir", key=f"del_doc_{doc['document_id']}", type="secondary"):
                                    with st.spinner("Excluindo..."):
                                        try:
                                            delete_response = requests.delete(
                                                f"{API_URL}/api/rag/documents/{doc['document_id']}",
                                                headers={"X-API-Key": API_KEY},
                                                timeout=10
                                            )
                                            delete_response.raise_for_status()
                                            st.success("✅ Documento excluído!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Erro: {str(e)}")
                            
                            st.divider()
                else:
                    st.info("📭 Nenhum documento na base de conhecimento")
            else:
                st.warning("⚠️ Erro ao carregar documentos")
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")

# TAB 3: Testar RAG
with tab3:
    st.header("🔍 Testar Busca RAG")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        query = st.text_input(
            "🔎 Query de Busca",
            placeholder="Ex: Quais são os horários de atendimento?",
            help="Digite sua pergunta ou termo de busca"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            top_k = st.slider("Número de Resultados (Top K)", 1, 20, 5)
        with col2:
            similarity_threshold = st.slider("Threshold de Similaridade", min_value=0.0, max_value=1.0, value=0.1, step=0.05, 
                                           help="Valores mais baixos retornam mais resultados (mais recall), valores mais altos retornam apenas resultados muito similares (mais precisão)")
        
        # Seleção de metadata para filtro RAG
        try:
            rag_metadata_filter = render_metadata_selector("rag_test")
        except Exception as e:
            # Se houver erro, continua sem filtro de metadata
            rag_metadata_filter = None
        
        if st.button("🔍 Buscar", type="primary"):
            if query:
                with st.spinner("Buscando na base de conhecimento..."):
                    result = search_rag(query, top_k, similarity_threshold, metadata_filter=rag_metadata_filter)
                
                if "error" in result:
                    st.error(f"❌ Erro: {result['error']}")
                else:
                    results = result.get("results", [])
                    
                    if results:
                        st.success(f"✅ Encontrados {len(results)} resultados")
                        
                        for i, res in enumerate(results, 1):
                            with st.expander(f"📄 Resultado {i} (Similaridade: {res.get('similarity', 0):.2%})"):
                                st.write("**Conteúdo:**")
                                st.write(res.get("content", ""))
                                
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.write(f"**Fonte:** {res.get('source', 'N/A')}")
                                with col_b:
                                    st.write(f"**Document ID:** {res.get('document_id', 'N/A')}")
                                
                                if res.get("metadata"):
                                    st.write("**Metadados:**")
                                    st.json(res.get("metadata"))
                    else:
                        st.warning("⚠️ Nenhum resultado encontrado")
                    
                    st.json(result)
            else:
                st.warning("⚠️ Digite uma query primeiro")
    
    with col2:
        st.subheader("💡 Exemplos de Queries")
        example_queries = [
            "horários de atendimento",
            "política de devolução",
            "como funciona o processo",
            "contato e suporte",
            "informações sobre produtos"
        ]
        
        for example in example_queries:
            if st.button(f"📝 {example}", key=f"example_{example}"):
                st.session_state.rag_query = example
                st.rerun()
        
        if "rag_query" in st.session_state:
            query = st.session_state.rag_query
            del st.session_state.rag_query

# TAB 4: Testes do Sistema
with tab4:
    st.header("🧪 Testes do Sistema")
    
    test_category = st.selectbox(
        "Categoria de Testes",
        [
            "🔌 Conectividade",
            "💬 Processamento de Mensagens",
            "📚 RAG (Base de Conhecimento)",
            "🔍 Busca Vetorial",
            "⚙️ Configuração",
            "🔄 Integração Completa"
        ]
    )
    
    if test_category == "🔌 Conectividade":
        st.subheader("Testes de Conectividade")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Testar Health Check"):
                with st.spinner("Testando..."):
                    try:
                        response = requests.get(f"{API_URL}/health", timeout=5)
                        if response.status_code == 200:
                            st.success("✅ Health Check OK")
                            st.json(response.json())
                        else:
                            st.error(f"❌ Status: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
        
        with col2:
            if st.button("Testar Info do Serviço"):
                with st.spinner("Testando..."):
                    try:
                        response = requests.get(f"{API_URL}/", timeout=5)
                        if response.status_code == 200:
                            st.success("✅ Serviço OK")
                            st.json(response.json())
                        else:
                            st.error(f"❌ Status: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
        
        with col3:
            if st.button("Testar Autenticação"):
                with st.spinner("Testando..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/api/message",
                            headers=HEADERS,
                            json={"message": "teste", "user_id": "test", "channel": "test"},
                            timeout=5
                        )
                        if response.status_code == 200:
                            st.success("✅ Autenticação OK")
                        elif response.status_code == 403:
                            st.error("❌ API Key inválida")
                        else:
                            st.warning(f"⚠️ Status: {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
    
    elif test_category == "💬 Processamento de Mensagens":
        st.subheader("Testes de Processamento de Mensagens")
        
        test_messages = [
            "Olá, como você está?",
            "Quais são seus horários de atendimento?",
            "Preciso de ajuda com meu pedido",
            "Como faço para cancelar?",
            "Quais são as formas de pagamento?"
        ]
        
        selected_message = st.selectbox("Selecione uma mensagem de teste", test_messages)
        custom_message = st.text_input("Ou digite uma mensagem customizada")
        
        message_to_test = custom_message if custom_message else selected_message
        
        if st.button("▶️ Executar Teste"):
            with st.spinner("Processando mensagem..."):
                start_time = time.time()
                result = send_message(message_to_test, "test_user", "test")
                elapsed_time = time.time() - start_time
            
            if "error" in result:
                st.error(f"❌ Erro: {result['error']}")
            else:
                st.success(f"✅ Resposta recebida em {elapsed_time:.2f}s")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Resposta:**")
                    st.write(result.get("response", ""))
                with col2:
                    st.write("**Métricas:**")
                    st.metric("Tempo de Resposta", f"{elapsed_time:.2f}s")
                    st.metric("Fontes", len(result.get("sources", [])))
                
                with st.expander("📋 Resposta Completa"):
                    st.json(result)
    
    elif test_category == "📚 RAG (Base de Conhecimento)":
        st.subheader("Testes de RAG")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Teste de Busca Simples**")
            if st.button("🔍 Busca Simples", key="rag_simple"):
                with st.spinner("Executando..."):
                    result = search_rag("teste", top_k=5)
                    if "error" in result:
                        st.error(f"❌ {result['error']}")
                    else:
                        st.success(f"✅ {len(result.get('results', []))} resultados")
                        st.json(result)
        
        with col2:
            st.write("**Teste de Busca Múltiplos Resultados**")
            if st.button("🔍 Busca Top 10", key="rag_multi"):
                with st.spinner("Executando..."):
                    result = search_rag("atendimento", top_k=10)
                    if "error" in result:
                        st.error(f"❌ {result['error']}")
                    else:
                        st.success(f"✅ {len(result.get('results', []))} resultados")
                        st.json(result)
        
        st.divider()
        
        st.write("**Teste de Upload**")
        st.info("Use a aba '📄 Base de Conhecimento' para fazer upload de documentos")
    
    elif test_category == "🔍 Busca Vetorial":
        st.subheader("Testes de Busca Vetorial")
        
        queries = st.text_area(
            "Queries para Testar (uma por linha)",
            value="horários de atendimento\npolítica de devolução\ncontato\nprodutos",
            help="Digite múltiplas queries, uma por linha"
        ).split("\n")
        
        if st.button("▶️ Executar Todas as Queries"):
            results_container = st.container()
            
            for query in queries:
                if query.strip():
                    with results_container:
                        st.write(f"**Query:** {query}")
                        with st.spinner(f"Buscando '{query}'..."):
                            result = search_rag(query.strip(), top_k=5)
                        
                        if "error" in result:
                            st.error(f"❌ {result['error']}")
                        else:
                            results = result.get("results", [])
                            st.write(f"✅ {len(results)} resultados encontrados")
                            
                            for i, res in enumerate(results, 1):
                                st.write(f"{i}. Similaridade: {res.get('similarity', 0):.2%}")
                        
                        st.divider()
    
    elif test_category == "⚙️ Configuração":
        st.subheader("Testes de Configuração")
        
        st.write("**Configurações Atuais:**")
        config_info = {
            "API URL": API_URL,
            "API Key": API_KEY[:20] + "..." if len(API_KEY) > 20 else API_KEY,
            "Health Check": "✅ Online" if check_api_health() else "❌ Offline"
        }
        st.json(config_info)
        
        if st.button("🔄 Verificar Todas as Configurações"):
            with st.spinner("Verificando..."):
                checks = {
                    "Health Check": check_api_health(),
                    "Autenticação": False,
                    "Endpoint de Mensagens": False,
                    "Endpoint RAG Upload": False,
                    "Endpoint RAG Search": False
                }
                
                # Testar autenticação
                try:
                    response = requests.post(
                        f"{API_URL}/api/message",
                        headers=HEADERS,
                        json={"message": "test", "user_id": "test", "channel": "test"},
                        timeout=5
                    )
                    checks["Autenticação"] = response.status_code != 403
                    checks["Endpoint de Mensagens"] = response.status_code == 200
                except:
                    pass
                
                # Mostrar resultados
                for check_name, status in checks.items():
                    if status:
                        st.success(f"✅ {check_name}")
                    else:
                        st.error(f"❌ {check_name}")
    
    elif test_category == "🔄 Integração Completa":
        st.subheader("Teste de Integração Completa")
        
        st.write("Este teste executa um fluxo completo:")
        st.write("1. Upload de documento")
        st.write("2. Busca na base de conhecimento")
        st.write("3. Processamento de mensagem usando RAG")
        
        if st.button("▶️ Executar Teste Completo", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Passo 1: Upload (simulado - precisa de arquivo real)
            status_text.text("Passo 1/3: Upload de documento...")
            progress_bar.progress(33)
            st.info("⚠️ Para teste completo, faça upload de um documento primeiro")
            
            # Passo 2: Busca
            status_text.text("Passo 2/3: Buscando na base de conhecimento...")
            progress_bar.progress(66)
            search_result = search_rag("teste", top_k=3)
            if "error" not in search_result:
                st.success(f"✅ Busca OK: {len(search_result.get('results', []))} resultados")
            
            # Passo 3: Processamento
            status_text.text("Passo 3/3: Processando mensagem...")
            progress_bar.progress(100)
            message_result = send_message("Teste de integração", "integration_test", "test")
            if "error" not in message_result:
                st.success("✅ Processamento OK")
                st.write("**Resposta:**", message_result.get("response", ""))
            
            status_text.text("✅ Teste completo finalizado!")
            progress_bar.progress(100)

if __name__ == "__main__":
    # Para rodar: streamlit run interface.py
    pass

