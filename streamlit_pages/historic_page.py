import streamlit as st
from backend import backend
from utils.models import KPIType
import pandas as pd

def _clean_float(val: str) -> float:
    """Converte string para float"""
    try:
        clean = str(val).replace("%", "").strip().replace(",", "").replace("_", "")
        if not clean:
            return 0.0
        return float(clean)
    except:
        return 0.0

def _get_cell_color(actual: str, target: str, kpi_type: KPIType) -> tuple:
    """Retorna background e cor do texto baseado na performance"""
    if str(actual) == "-" or str(target) == "-":
        return "#F3F4F6", "#6B7280"  # Neutral
    
    try:
        val_f = _clean_float(actual)
        tgt_f = _clean_float(target)
        type_str = str(kpi_type.value if isinstance(kpi_type, KPIType) else kpi_type).upper()
        
        if "TEXT" in type_str:
            is_bad = str(actual).lower() != str(target).lower()
        elif "LOWER" in type_str:
            is_bad = val_f > tgt_f
        else:
            is_bad = val_f < tgt_f
        
        if is_bad:
            return "#FEE2E2", "#991B1B"  # Red
        else:
            return "#D1FAE5", "#065F46"  # Green
    except:
        return "#F3F4F6", "#6B7280"  # Neutral

def render_month_cell(month_data: dict, kpi_type: KPIType):
    """Renderiza uma célula de mês"""
    bg_color, txt_color = _get_cell_color(month_data['actual'], month_data['target'], kpi_type)
    
    st.markdown(f"""
    <div style="
        background-color: {bg_color};
        border-radius: 0.3rem;
        padding: 0.8rem;
        text-align: center;
        min-width: 80px;
        margin: 0.2rem;
    ">
        <div style="font-size: 0.7rem; font-weight: bold; color: #9CA3AF; margin-bottom: 0.3rem;">
            {month_data['name'].upper()}
        </div>
        <div style="font-size: 1.3rem; font-weight: bold; color: {txt_color}; margin: 0.3rem 0;">
            {month_data['actual']}
        </div>
        <div style="font-size: 0.8rem; color: #6B7280;">
            T: {month_data['target']}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render():
    """Renderiza a página de histórico"""
    
    if not st.session_state.selected_sector or st.session_state.selected_sector == "":
        # Placeholder quando nenhum setor selecionado
        st.markdown('<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 400px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 4rem; color: #D1D5DB; margin-bottom: 1rem;">📜</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 1.5rem; color: #9CA3AF; font-weight: 300;">SELECT A DEPARTMENT</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Carrega dados históricos
        with st.spinner(f'Loading historic data for {st.session_state.selected_sector}...'):
            try:
                data = backend.load_historic_data(st.session_state.selected_sector)
                
                if not data:
                    st.warning(f"No historic data found for {st.session_state.selected_sector}")
                else:
                    st.info(f"📜 {len(data)} KPIs loaded for **{st.session_state.selected_sector}**")
                    
                    # Renderiza cada KPI
                    for item in data:
                        st.markdown('<div style="margin-bottom: 1rem;">', unsafe_allow_html=True)
                        
                        # Container principal com informações + meses
                        col_info, col_months = st.columns([3, 9])
                        
                        with col_info:
                            # Card de informações do KPI
                            st.markdown("""
                            <div style="background-color: #FFFFFF; border-radius: 0.3rem; padding: 1rem; min-height: 150px; border: 1px solid #E5E7EB;">
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div style="font-size: 1rem; font-weight: bold; color: #1F2937; margin-bottom: 0.5rem;">
                                {item['name']}
                            </div>
                            <div style="font-size: 0.75rem; color: #9CA3AF; margin-bottom: 1rem;">
                                Unit: <span style="font-weight: bold; color: #6B7280;">{item.get('unit', '-')}</span>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Métricas em grid
                            st.markdown('<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem;">', unsafe_allow_html=True)
                            
                            # YTD 2025
                            st.markdown(f"""
                            <div>
                                <div style="font-size: 0.65rem; color: #9CA3AF; font-weight: bold;">YTD 2025</div>
                                <div style="font-size: 1rem; color: #111827; font-weight: bold;">{item.get('ytd', '-')}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # '24 Result
                            st.markdown(f"""
                            <div>
                                <div style="font-size: 0.65rem; color: #9CA3AF; font-weight: bold;">'24 RESULT</div>
                                <div style="font-size: 1rem; color: #6B7280;">{item.get('res_2024', '-')}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # '25 Target
                            st.markdown(f"""
                            <div>
                                <div style="font-size: 0.65rem; color: #9CA3AF; font-weight: bold;">'25 TARGET</div>
                                <div style="font-size: 1rem; color: #6B7280;">{item.get('target_2025', '-')}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # '25 Challenge
                            st.markdown(f"""
                            <div>
                                <div style="font-size: 0.65rem; color: #9CA3AF; font-weight: bold;">'25 CHALLENGE</div>
                                <div style="font-size: 1rem; color: #EA580C; font-weight: bold;">{item.get('challenge_2025', '-')}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)  # Fecha grid
                            st.markdown('</div>', unsafe_allow_html=True)  # Fecha card
                        
                        with col_months:
                            # Células dos meses em scroll horizontal
                            st.markdown('<div style="display: flex; overflow-x: auto; gap: 0.3rem; padding: 0.5rem; background-color: #F9FAFB; border-radius: 0.3rem;">', unsafe_allow_html=True)
                            
                            # Cria colunas para os 12 meses
                            month_cols = st.columns(12)
                            for m_idx, col in enumerate(month_cols, start=1):
                                m_data = item['months'][m_idx]
                                with col:
                                    render_month_cell(m_data, item['type'])
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown('<hr style="border: none; border-top: 1px solid #E5E7EB; margin: 1.5rem 0;">', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"❌ Error loading historic data: {e}")
                import traceback
                st.code(traceback.format_exc())

