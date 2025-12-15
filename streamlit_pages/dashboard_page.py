import streamlit as st
from backend import backend
from datetime import date
from dateutil.relativedelta import relativedelta
from utils.constants import MONTH_NAMES, MONTH_OPTIONS
from typing import Optional, Dict, Any, List

def _is_kpi_bad(actual, target, kpi_type) -> bool:
    """Verifica se o KPI está ruim"""
    try:
        def clean_float(val):
            clean = str(val).replace("%", "").strip().replace(",", "").replace("_", "")
            return float(clean) if clean else 0.0

        if kpi_type.value == 'TEXT':
            return str(actual).lower() != str(target).lower()
        val_f = clean_float(actual)
        tgt_f = clean_float(target)
        if kpi_type.value == 'LOWER_THAN':
            return val_f > tgt_f
        else:
            return val_f < tgt_f
    except:
        return True

def _calculate_dashboard_metrics(month_idx: int, sector_filter: str, available_sectors: List[str]) -> Optional[Dict[str, Any]]:
    """Calcula métricas do dashboard"""
    all_kpis_data = []
    sectors_to_load = [s for s in available_sectors if s != "ALL DEPARTMENTS"] if sector_filter == "ALL DEPARTMENTS" else [sector_filter]

    for sector in sectors_to_load:
        historic_data = backend.load_historic_data(sector)
        all_kpis_data.extend(historic_data)

    if not all_kpis_data:
        return None

    total_kpis = 0
    kpis_on_target = 0
    kpi_scores = []

    for item in all_kpis_data:
        month_data = item['months'].get(month_idx)
        if not month_data or str(month_data['actual']) == "-" or str(month_data['target']) == "-":
            continue 

        total_kpis += 1
        is_bad = _is_kpi_bad(month_data['actual'], month_data['target'], item['type'])
        if not is_bad:
            kpis_on_target += 1

        score = 0.0
        try:
            val_f = float(str(month_data['actual']).replace('%', '').replace(',',''))
            tgt_f = float(str(month_data['target']).replace('%', '').replace(',',''))
            if tgt_f != 0:
                if item['type'].value == 'LOWER_THAN':
                    score = (tgt_f / val_f) if val_f > 0 else 0 
                else:
                    score = val_f / tgt_f
            else:
                score = 1.0 if not is_bad else 0.0
        except:
            score = 0.0

        kpi_scores.append({"name": item['name'], "score": score, "status": "Red" if is_bad else "Green"})

    ranked_scores = sorted([s for s in kpi_scores if s['score'] != 0.0], key=lambda x: x['score'], reverse=True)
    top_kpis = ranked_scores[:3]
    bottom_kpis = ranked_scores[-3:]
    if len(ranked_scores) > 3 and ranked_scores[0]['score'] < 1.0:
        bottom_kpis = ranked_scores

    return {
        "total_kpis": total_kpis,
        "on_target": kpis_on_target,
        "needs_action": total_kpis - kpis_on_target,
        "perc_on_target": f"{kpis_on_target / total_kpis * 100:.1f}%" if total_kpis > 0 else "0.0%",
        "top_kpis": top_kpis,
        "bottom_kpis": bottom_kpis,
        "month_idx": month_idx
    }

def render_summary_card(title: str, value: str, sub_title: str, icon: str, color: str):
    """Renderiza um card de sumário"""
    st.markdown(f"""
    <div style="
        background-color: #FFFFFF;
        border-radius: 0.5rem;
        padding: 1.5rem;
        border: 1px solid #E5E7EB;
        min-height: 150px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
            <div style="font-size: 0.8rem; color: #9CA3AF; font-weight: bold;">
                {title.upper()}
            </div>
            <div style="font-size: 1.5rem;">
                {icon}
            </div>
        </div>
        <div style="font-size: 2.5rem; font-weight: bold; color: {color}; margin: 1rem 0;">
            {value}
        </div>
        <div style="font-size: 0.9rem; color: #6B7280;">
            {sub_title}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_ranked_kpi_list(title: str, kpis: List[Dict[str, Any]], is_top: bool = True):
    """Renderiza lista ranqueada de KPIs"""
    color = "#10B981" if is_top else "#EF4444"
    
    st.markdown(f"""
    <div style="
        background-color: #FFFFFF;
        border-radius: 0.5rem;
        padding: 1.5rem;
        border: 1px solid #E5E7EB;
        min-height: 300px;
    ">
        <div style="font-size: 1.2rem; font-weight: bold; color: #111827; margin-bottom: 1rem;">
            {title}
        </div>
        <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 1rem 0;">
    """, unsafe_allow_html=True)
    
    if not kpis:
        st.markdown('<div style="color: #9CA3AF; text-align: center; padding: 2rem;">No data to display.</div>', unsafe_allow_html=True)
    else:
        for item in kpis:
            score_text = f"({item['score'] * 100:.1f}%)"
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0;">
                <div style="font-size: 0.95rem; color: #374151; flex: 1;">
                    {item['name']}
                </div>
                <div style="font-size: 0.95rem; color: {color}; font-weight: bold;">
                    {score_text}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render():
    """Renderiza a página de Dashboard"""
    
    # Inicializa session state para filtros do dashboard
    if 'dashboard_month' not in st.session_state:
        last_month_dt = date.today() - relativedelta(months=1)
        st.session_state.dashboard_month = last_month_dt.strftime('%B')
    
    if 'dashboard_sector' not in st.session_state:
        st.session_state.dashboard_sector = "ALL DEPARTMENTS"
    
    # Título
    st.markdown(f"""
    <div style="font-size: 1.5rem; font-weight: bold; color: #111827; margin-bottom: 1.5rem;">
        EXECUTIVE SUMMARY - {st.session_state.dashboard_month.upper()}
    </div>
    """, unsafe_allow_html=True)
    
    # Filtros
    col1, col2, col3 = st.columns([2, 2, 8])
    
    with col1:
        month_selected = st.selectbox(
            "Evaluation Month",
            options=MONTH_NAMES,
            index=MONTH_NAMES.index(st.session_state.dashboard_month) if st.session_state.dashboard_month in MONTH_NAMES else 0,
            key="dashboard_month_selector"
        )
        if month_selected != st.session_state.dashboard_month:
            st.session_state.dashboard_month = month_selected
            st.rerun()
    
    # Prepara lista de setores para dashboard
    available_sectors_dash = ["ALL DEPARTMENTS"] + [s for s in st.session_state.available_sectors if s != ""]
    
    with col2:
        sector_selected = st.selectbox(
            "Department Scope",
            options=available_sectors_dash,
            index=available_sectors_dash.index(st.session_state.dashboard_sector) if st.session_state.dashboard_sector in available_sectors_dash else 0,
            key="dashboard_sector_selector"
        )
        if sector_selected != st.session_state.dashboard_sector:
            st.session_state.dashboard_sector = sector_selected
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Calcula métricas
    with st.spinner('📊 Calculating analytics...'):
        try:
            month_idx = MONTH_OPTIONS.get(st.session_state.dashboard_month, 1)
            data = _calculate_dashboard_metrics(month_idx, st.session_state.dashboard_sector, available_sectors_dash)
            
            if data is None:
                st.warning("No data available for the selected filters")
                return
            
            # Cards de sumário
            col1, col2, col3 = st.columns(3)
            
            with col1:
                render_summary_card(
                    title="TOTAL KPIS",
                    value=str(data['total_kpis']),
                    sub_title="KPIs found",
                    icon="📊",
                    color="#111827"
                )
            
            with col2:
                render_summary_card(
                    title="ON TARGET",
                    value=str(data['on_target']),
                    sub_title=f"Achieved ({data['perc_on_target']})",
                    icon="✅",
                    color="#10B981"
                )
            
            with col3:
                render_summary_card(
                    title="NEEDS ACTION",
                    value=str(data['needs_action']),
                    sub_title="Requires justification",
                    icon="⚠️",
                    color="#EF4444"
                )
            
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # Rankings
            col1, col2 = st.columns(2)
            
            with col1:
                render_ranked_kpi_list(
                    title="TOP 3 PERFORMERS",
                    kpis=data['top_kpis'],
                    is_top=True
                )
            
            with col2:
                render_ranked_kpi_list(
                    title="BOTTOM 3 PERFORMERS",
                    kpis=data['bottom_kpis'],
                    is_top=False
                )
                
        except Exception as e:
            st.error(f"❌ Error calculating dashboard metrics: {e}")
            import traceback
            st.code(traceback.format_exc())

