import streamlit as st
from backend import backend
from utils.models import KPI, KPIType
from datetime import date

def render_kpi_card(kpi: KPI, sector: str):
    """Renderiza um card de KPI individual"""
    
    # Verifica se o KPI já foi salvo
    is_locked = kpi.curr_value and str(kpi.curr_value).strip() != ""
    
    # Card container
    with st.container():
        st.markdown(f'<div class="kpi-card">', unsafe_allow_html=True)
        
        # Título e descrição
        st.markdown(f'<div class="kpi-title">{kpi.name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-description">{kpi.description}</div>', unsafe_allow_html=True)
        
        # Métricas em colunas
        col1, col2, sep, col3, col4, col5 = st.columns([1.5, 1.5, 0.2, 1.5, 1.5, 1.5])
        
        with col1:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Prev Target</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{kpi.prev_target}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # Prev Achieved com cor
            prev_is_bad = _is_performance_bad(kpi.prev_achieved, kpi.prev_target, kpi.type)
            prev_color = "#EF4444" if prev_is_bad else "#10B981"
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Prev Achieved</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value" style="color: {prev_color}; font-weight: bold;">{kpi.prev_achieved}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with sep:
            st.markdown('<div style="height: 80px; border-left: 2px solid #E5E7EB; margin: 0 1rem;"></div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Target</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value" style="color: #111827; font-weight: bold;">{kpi.curr_target}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            # Actual - input ou display
            if is_locked:
                curr_is_bad = _is_performance_bad(kpi.curr_value, kpi.curr_target, kpi.type)
                curr_color = "#EF4444" if curr_is_bad else "#10B981"
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Actual</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="metric-value" style="color: {curr_color}; font-weight: bold;">{kpi.curr_value}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-label" style="text-align: center; margin-bottom: 0.5rem;">ACTUAL</div>', unsafe_allow_html=True)
                current_value = st.text_input(
                    "Actual Value",
                    value=kpi.curr_value if kpi.curr_value else "",
                    key=f"input_{sector}_{kpi.id}",
                    label_visibility="collapsed"
                )
                kpi.curr_value = current_value
        
        with col5:
            st.markdown('<br>', unsafe_allow_html=True)
            if is_locked:
                st.markdown('<span class="status-badge status-grey">SAVED</span>', unsafe_allow_html=True)
            else:
                # Verifica se deve justificar
                if kpi.curr_value and str(kpi.curr_value).strip():
                    is_bad = _is_performance_bad(kpi.curr_value, kpi.curr_target, kpi.type)
                    
                    if is_bad:
                        # Precisa justificar
                        if st.button("JUSTIFY", key=f"justify_btn_{sector}_{kpi.id}", use_container_width=True, type="secondary"):
                            st.session_state[f"justifying_{sector}_{kpi.id}"] = True
                            st.rerun()
                    else:
                        # Pode enviar direto
                        if st.button("SEND", key=f"send_btn_{sector}_{kpi.id}", use_container_width=True, type="primary"):
                            backend.save_kpi(kpi, sector=sector)
                            st.success(f"✅ KPI {kpi.name} salvo!")
                            st.rerun()
                else:
                    st.button("SEND", key=f"send_disabled_{sector}_{kpi.id}", disabled=True, use_container_width=True)
        
        # Formulário de justificativa (se necessário)
        if st.session_state.get(f"justifying_{sector}_{kpi.id}", False):
            st.markdown('<div style="background-color: #18181B; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;">', unsafe_allow_html=True)
            
            st.markdown(f'<div style="color: #EF4444; font-weight: bold; margin-bottom: 0.5rem;">⚠️ ACTION REQUIRED</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="color: #D4D4D8; font-size: 0.9rem; margin-bottom: 1rem;">Result \'{kpi.curr_value}\' needs justification against target \'{kpi.curr_target}\'.</div>', unsafe_allow_html=True)
            
            col_j1, col_j2, col_j3 = st.columns([3, 3, 2])
            
            with col_j1:
                justification = st.text_area("Root Cause", height=150, key=f"just_{sector}_{kpi.id}")
            
            with col_j2:
                countermeasure = st.text_area("Countermeasure", height=150, key=f"counter_{sector}_{kpi.id}")
            
            with col_j3:
                cm_date = st.date_input("Due Date", value=date.today(), key=f"date_{sector}_{kpi.id}")
                cm_resp = st.text_input("Responsible", key=f"resp_{sector}_{kpi.id}")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("SAVE", key=f"save_just_{sector}_{kpi.id}", use_container_width=True, type="primary"):
                        kpi.justification = justification
                        kpi.countermeasure = countermeasure
                        kpi.countermeasure_date = str(cm_date)
                        kpi.countermeasure_resp = cm_resp
                        backend.save_kpi(kpi, sector=sector)
                        st.session_state[f"justifying_{sector}_{kpi.id}"] = False
                        st.success(f"✅ KPI {kpi.name} salvo com justificativa!")
                        st.rerun()
                
                with col_btn2:
                    if st.button("CANCEL", key=f"cancel_just_{sector}_{kpi.id}", use_container_width=True):
                        st.session_state[f"justifying_{sector}_{kpi.id}"] = False
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

def _clean_float(val: str) -> float:
    """Converte string para float"""
    try:
        clean = str(val).replace("%", "").strip().replace(",", "").replace("_", "")
        if not clean:
            return 0.0
        return float(clean)
    except:
        return 0.0

def _is_performance_bad(value: str, target: str, kpi_type: KPIType) -> bool:
    """Verifica se a performance está ruim"""
    if not value or not str(value).strip():
        return False
    
    try:
        type_str = str(kpi_type.value if isinstance(kpi_type, KPIType) else kpi_type).upper()
        
        if "TEXT" in type_str:
            return str(value).strip().lower() != str(target).strip().lower()
        
        val_f = _clean_float(value)
        tgt_f = _clean_float(target)
        
        if "LOWER" in type_str:
            return val_f > tgt_f
        else:
            return val_f < tgt_f
    except:
        return True

def render():
    """Renderiza a página de Insert Results"""
    
    if not st.session_state.selected_sector or st.session_state.selected_sector == "":
        # Placeholder quando nenhum setor selecionado
        st.markdown('<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 400px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 4rem; color: #D1D5DB; margin-bottom: 1rem;">📊</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 1.5rem; color: #9CA3AF; font-weight: 300;">SELECT A DEPARTMENT</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Carrega KPIs do setor selecionado
        with st.spinner(f'Loading KPIs for {st.session_state.selected_sector}...'):
            try:
                kpis = backend.load_data(st.session_state.selected_sector)
                
                if not kpis:
                    st.warning(f"No KPIs found for {st.session_state.selected_sector}")
                else:
                    st.info(f"📊 {len(kpis)} KPIs loaded for **{st.session_state.selected_sector}**")
                    
                    # Renderiza cada KPI
                    for kpi in kpis:
                        render_kpi_card(kpi, st.session_state.selected_sector)
                    
            except Exception as e:
                st.error(f"❌ Error loading KPIs: {e}")
                import traceback
                st.code(traceback.format_exc())

