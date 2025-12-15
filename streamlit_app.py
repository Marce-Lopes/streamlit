import streamlit as st
from pathlib import Path
import datetime
import time
import base64
from backend import backend
from utils.models import KPI
from streamlit_pages import insert_results_page, historic_page, dashboard_page

# Configuração da página
st.set_page_config(
    page_title="PMO Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"  # Sidebar sempre aberta
)

# CSS Customizado para replicar visual do Rio
st.markdown("""
<style>
    /* Remove padding padrão */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    
    /* Header escuro */
    .main-header {
        background-color: #000000;
        padding: 1.2rem;
        border-radius: 0;
        margin: -1rem -1rem 2rem -1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .header-title {
        color: #FFFFFF;
        font-size: 1.0rem;
        font-weight: 300;
        margin: 0;
    }
    
    .header-subtitle {
        color: #D1D5DB;
        font-size: 0.6rem;
        font-weight: 300;
        margin: 0;
    }
    
    /* Esconde header do Streamlit completamente */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Sidebar customizada - SEMPRE VISÍVEL e ULTRA COMPACTA */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        padding-top: 0.1rem !important;
        padding-bottom: 0.25rem !important;
        min-width: 21rem !important;
        max-width: 21rem !important;
        overflow-y: hidden !important;  /* SEM scroll */
    }
    
    /* Remove TODO espaço do topo da sidebar */
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    
    /* Remove padding de todos os elementos filhos */
    [data-testid="stSidebar"] > div {
        padding-top: 0rem !important;
    }
    
    /* Ajusta logo da sidebar - COLADO no topo */
    [data-testid="stSidebar"] img {
        margin-top: 0rem !important;
        margin-bottom: 0.1rem !important;
    }
    
    /* Remove espaços extras do título */
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        margin-top: 0.1rem !important;
        margin-bottom: 0.1rem !important;
        line-height: 1.1 !important;
        padding: 0 !important;
    }
    
    /* Remove TODOS espaços entre elementos */
    [data-testid="stSidebar"] .stMarkdown {
        margin-top: 0rem !important;
        margin-bottom: 0rem !important;
        padding: 0 !important;
    }
    
    /* Botões ULTRA compactos */
    [data-testid="stSidebar"] .stButton {
        margin-top: 0.1rem !important;
        margin-bottom: 0.1rem !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        padding: 0.3rem 0.8rem !important;
        margin: 0 !important;
        font-size: 0.9rem !important;
        min-height: 2rem !important;
    }
    
    /* Divisores ULTRA compactos */
    [data-testid="stSidebar"] hr {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
        border-width: 1px !important;
    }
    
    /* Status card ULTRA compacto */
    [data-testid="stSidebar"] .stMarkdown > div {
        margin: 0.1rem 0 !important;
        padding: 0 !important;
    }
    
    /* Remove espaços de containers */
    [data-testid="stSidebar"] > div > div {
        gap: 0rem !important;
    }
    
    /* Captions menores */
    [data-testid="stSidebar"] .stCaption {
        margin-top: 0.1rem !important;
        margin-bottom: 0.1rem !important;
        padding: 0 !important;
    }
    
    /* Remove botão de fechar sidebar (<<) - Sidebar sempre aberta */
    [data-testid="stSidebar"] button[aria-label*="Close"],
    [data-testid="stSidebar"] button[aria-label*="close"],
    [data-testid="stSidebar"] button[title*="Close"],
    [data-testid="stSidebar"] button[title*="close"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Garante que sidebar não pode ser escondida */
    [data-testid="stSidebar"][aria-expanded="false"] {
        display: block !important;
        transform: translateX(0) !important;
        visibility: visible !important;
    }
    
    /* Remove qualquer controle de colapsar */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Botões personalizados */
    .stButton button {
        border-radius: 0.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Botões primários */
    button[kind="primary"] {
        background: linear-gradient(135deg, #36454F 0%, #2c3640 100%);
        color: white;
        box-shadow: 0 2px 4px rgba(54,69,79,0.3);
    }
    
    /* Botões secundários */
    button[kind="secondary"] {
        background-color: #F3F4F6;
        color: #374151;
    }
    
    button[kind="secondary"]:hover {
        background-color: #E5E7EB;
    }
    
    /* Cards de KPI */
    .kpi-card {
        background-color: #FFFFFF;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #E5E7EB;
    }
    
    .kpi-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #111827;
        margin-bottom: 0.5rem;
    }
    
    .kpi-description {
        font-size: 0.8rem;
        color: #6B7280;
        margin-bottom: 1rem;
    }
    
    /* Status badges */
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        font-weight: 700;
        display: inline-block;
    }
    
    .status-green {
        background-color: #10B981;
        color: white;
    }
    
    .status-red {
        background-color: #EF4444;
        color: white;
    }
    
    .status-grey {
        background-color: #6B7280;
        color: white;
    }
    
    /* Métricas */
    .metric-container {
        text-align: center;
        padding: 1rem;
    }
    
    .metric-label {
        font-size: 0.65rem;
        color: #6B7280;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    .metric-value {
        font-size: 1.3rem;
        font-weight: bold;
        margin-top: 0.3rem;
    }
    
    /* Background */
    .main {
        background-color: #FFFAFA;
    }
    
    /* Divisor */
    .divider {
        height: 1px;
        background-color: #E5E7EB;
        margin: 2.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização do Session State
if 'page' not in st.session_state:
    st.session_state.page = 'insert'

if 'selected_sector' not in st.session_state:
    st.session_state.selected_sector = ''

if 'pending_count' not in st.session_state:
    st.session_state.pending_count = backend.get_pending_count()

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.datetime.now().strftime("%H:%M")

if 'last_refresh_timestamp' not in st.session_state:
    st.session_state.last_refresh_timestamp = time.time()

if 'available_sectors' not in st.session_state:
    try:
        raw_sectors = backend.get_available_sectors()
        st.session_state.available_sectors = [''] + raw_sectors
    except Exception as e:
        st.session_state.available_sectors = ['']

# 🆕 Auto-refresh: Verifica se passou 15 minutos desde último refresh
AUTO_REFRESH_INTERVAL = 900  # 900 segundos = 15 minutos
current_time = time.time()
time_since_last_refresh = current_time - st.session_state.last_refresh_timestamp

if time_since_last_refresh > AUTO_REFRESH_INTERVAL:
    # Passou 15 minutos, faz refresh automático silencioso
    print(f"⏰ [Auto-Refresh] {int(time_since_last_refresh/60)} minutos desde último refresh. Atualizando...")
    try:
        backend._refresh_cache_if_needed(force=False)  # Refresh normal (não forçado)
        st.session_state.pending_count = backend.get_pending_count()
        st.session_state.last_refresh = datetime.datetime.now().strftime("%H:%M")
        st.session_state.last_refresh_timestamp = time.time()
        
        # Atualiza lista de setores
        raw_sectors = backend.get_available_sectors()
        st.session_state.available_sectors = [''] + raw_sectors
    except Exception as e:
        print(f"❌ [Auto-Refresh] Erro: {e}")

# Função para trocar de página
def navigate_to(page_name):
    st.session_state.page = page_name

# Função de refresh manual
def manual_refresh():
    """Executa refresh manual dos dados do SharePoint"""
    with st.spinner('🔄 Atualizando dados do SharePoint...'):
        try:
            success = backend.force_refresh_from_sharepoint()
            st.session_state.pending_count = backend.get_pending_count()
            st.session_state.last_refresh = datetime.datetime.now().strftime("%H:%M")
            
            # Atualiza lista de setores
            raw_sectors = backend.get_available_sectors()
            st.session_state.available_sectors = [''] + raw_sectors
            
            if success:
                st.success(f"✅ Dados atualizados! Pendências: {st.session_state.pending_count}")
            else:
                st.warning("⚠️ Refresh falhou, usando cache local")
                
        except Exception as e:
            st.error(f"❌ Erro ao atualizar: {e}")
    
    st.rerun()

# ============== SIDEBAR ==============
with st.sidebar:
    # Logo e título (ULTRA colado no topo)
    logo_path = Path(__file__).parent / "wlogo.png"
    if logo_path.exists():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(str(logo_path), width=45)  # Logo ainda menor
    
    st.markdown('<h2 style="text-align: center; margin: 0rem; padding: 0rem; font-size: 1rem; line-height: 1.1;">PMO ANALYTICS</h2>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Navegação (colado e compacto)
    st.markdown("### 📋 MENU")
    
    # Insert Results
    if st.button("📝  Insert Results", key="btn_insert", use_container_width=True, 
                type="primary" if st.session_state.page == 'insert' else "secondary"):
        st.session_state.page = 'insert'
        st.rerun()
    
    # Historic
    if st.button("📜  Historic", key="btn_historic", use_container_width=True,
                type="primary" if st.session_state.page == 'historic' else "secondary"):
        st.session_state.page = 'historic'
        st.rerun()
    
    # Dashboard
    if st.button("📊  Dashboard", key="btn_dashboard", use_container_width=True,
                type="primary" if st.session_state.page == 'dashboard' else "secondary"):
        st.session_state.page = 'dashboard'
        st.rerun()
    
    st.markdown("---")
    
    # Botão de Refresh
    if st.button("🔄 Refresh Data", key="btn_refresh", use_container_width=True):
        manual_refresh()
    
    st.markdown("---")
    
    # Status com card (MÍNIMO possível)
    st.markdown("### ⚙️ STATUS")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
        padding: 0.4rem;
        border-radius: 0.4rem;
        border-left: 3px solid #36454F;
        margin: 0.1rem 0;
    ">
        <div style="color: #374151; font-size: 0.7rem; margin-bottom: 0.2rem; line-height: 1.2;">
            ⏰ <strong>Last:</strong> {st.session_state.last_refresh}
        </div>
        <div style="color: {'#F59E0B' if st.session_state.pending_count > 0 else '#10B981'}; font-size: 0.7rem; line-height: 1.2;">
            {'⚠️' if st.session_state.pending_count > 0 else '✅'} <strong>Pending:</strong> {st.session_state.pending_count}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer (compacto)
    st.markdown("---")
    st.markdown('<div style="font-size: 0.65rem; color: #9CA3AF; margin-top: 0.1rem; margin-bottom: 0.1rem;">PMO Data Analytics v2.0</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 0.65rem; color: #9CA3AF; margin: 0;">Powered by Streamlit</div>', unsafe_allow_html=True)

# ============== MAIN CONTENT ==============

# Header Estilo Rio (Preto com Logo)
page_titles = {
    'insert': 'PERFORMANCE INPUT',
    'historic': 'HISTORIC DATA',
    'dashboard': 'EXECUTIVE DASHBOARD'
}

logo_path = Path(__file__).parent / "wlogo.png"
logo_exists = logo_path.exists()

# Header com logo e título
st.markdown("""
<style>
    /* Esconde header do Streamlit completamente */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Força o botão de expandir (quando sidebar fechada) a ficar visível */
    [data-testid="collapsedControl"] {
        display: block !important;
        visibility: visible !important;
        position: fixed !important;
        left: 0 !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        z-index: 999999 !important;
        background: rgba(54, 69, 79, 0.95) !important;
        border: none !important;
        border-radius: 0 0.5rem 0.5rem 0 !important;
        padding: 1rem 0.5rem !important;
        box-shadow: 2px 0 8px rgba(0,0,0,0.3) !important;
        cursor: pointer !important;
    }
    
    [data-testid="collapsedControl"]:hover {
        background: #36454F !important;
        box-shadow: 2px 0 12px rgba(0,0,0,0.5) !important;
    }
    
    [data-testid="collapsedControl"] svg {
        fill: white !important;
        width: 20px !important;
        height: 20px !important;
    }
    
    
    .main > div:first-child {
        padding-top: 0.5rem !important;
    }
    
    /* Remove apenas elementos desnecessários */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Remove deploy button do canto superior direito */
    div[data-testid="stToolbar"] {
        display: none;
    }
    
    /* Header customizado */
    .custom-header {
        background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
        padding: 1.5rem 2rem;
        margin: -1rem -1rem 2rem -1rem;
        border-bottom: 3px solid #36454F;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        position: relative;
        z-index: 1;  /* Baixo para não cobrir botões nativos */
    }
    
    /* Sidebar sempre visível por padrão */
    [data-testid="stSidebar"][aria-expanded="false"] {
        transform: translateX(0) !important;
    }
    
    /* Garante que o elemento existe no DOM mesmo quando "colapsado" */
    section[data-testid="stSidebar"] {
        min-width: 0 !important;
    }
    
    .header-logo {
        width: 50px;
        height: 50px;
        object-fit: contain;
    }
    
    .header-text-container {
        text-align: center;
    }
    
    .header-main-title {
        color: #FFFFFF;
        font-size: 1.1rem;
        font-weight: 300;
        letter-spacing: 1px;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .header-sub-title {
        color: #D1D5DB;
        font-size: 0.7rem;
        font-weight: 300;
        letter-spacing: 2px;
        margin: 0;
        margin-top: 2px;
    }
</style>
""", unsafe_allow_html=True)

# Renderiza header
if logo_exists:
    with open(logo_path, "rb") as img_file:
        logo_b64 = base64.b64encode(img_file.read()).decode()
    
    st.markdown(f"""
    <div class="custom-header">
        <img src="data:image/png;base64,{logo_b64}" class="header-logo">
        <div class="header-text-container">
            <div class="header-main-title">{page_titles.get(st.session_state.page, 'PMO ANALYTICS')}</div>
            <div class="header-sub-title">PMO ANALYTICS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="custom-header">
        <div class="header-text-container">
            <div class="header-main-title">{page_titles.get(st.session_state.page, 'PMO ANALYTICS')}</div>
            <div class="header-sub-title">PMO ANALYTICS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Dropdown de setor (apenas para insert e historic)
if st.session_state.page in ['insert', 'historic']:
    col1, col2, col3 = st.columns([1, 2, 8])
    with col1:
        st.markdown("**DEPT:**")
    with col2:
        selected = st.selectbox(
            "Department",
            options=st.session_state.available_sectors,
            index=st.session_state.available_sectors.index(st.session_state.selected_sector) 
                  if st.session_state.selected_sector in st.session_state.available_sectors else 0,
            label_visibility="collapsed",
            key="sector_selector"
        )
        if selected != st.session_state.selected_sector:
            st.session_state.selected_sector = selected
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)

# Renderiza a página correspondente
if st.session_state.page == 'insert':
    insert_results_page.render()
elif st.session_state.page == 'historic':
    historic_page.render()
elif st.session_state.page == 'dashboard':
    dashboard_page.render()

