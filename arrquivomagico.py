import os

# Estrutura do Projeto e Conteúdo dos Arquivos
project_structure = {
    "utils": {
        "__init__.py": "",
        "styles.py": """
import rio

# --- TYPOGRAPHY ---
TITLE_STYLE = rio.TextStyle(font_weight="normal", fill=rio.Color.from_hex("#111827"))
BODY_STYLE = rio.TextStyle(fill=rio.Color.from_hex("#374151"))
MENU_TEXT_STYLE = rio.TextStyle(font_size=1.0, font_weight="normal", fill=rio.Color.from_hex("#374151"))

# --- COLORS ---
COLOR_RED = rio.Color.from_hex("#DC2626")
COLOR_GREEN = rio.Color.from_hex("#059669")
COLOR_GREY_TXT = rio.Color.from_hex("#374151")
COLOR_DISABLED = rio.Color.from_hex("#9CA3AF")
COLOR_LOCKED = rio.Color.from_hex("#6B7280")
BG_RED_LIGHT = rio.Color.from_hex("#FEE2E2")
BG_GREEN_LIGHT = rio.Color.from_hex("#D1FAE5")
BG_NEUTRAL = rio.Color.from_hex("#F3F4F6")
""",
        "models.py": """
from dataclasses import dataclass
from enum import Enum

class KPIType(Enum):
    TEXT = "TEXT"
    GREATER_THAN = "GREATER_THAN"
    LOWER_THAN = "LOWER_THAN"

@dataclass
class KPI:
    id: str
    name: str
    description: str
    type: KPIType
    prev_target: str
    prev_achieved: str
    curr_target: str
    curr_value: str = ""
    justification: str = ""
    countermeasure: str = ""
    countermeasure_date: str = ""
    countermeasure_resp: str = ""
""",
        "constants.py": """
MONTH_OPTIONS = {
    "January": 1, "February": 2, "March": 3, "April": 4, 
    "May": 5, "June": 6, "July": 7, "August": 8, 
    "September": 9, "October": 10, "November": 11, "December": 12
}
MONTH_NAMES = list(MONTH_OPTIONS.keys())
SECTORS = ["Commercial", "Channel", "After Sales", "Brand", "GTM", "Logistic", "PPD", "Sales"]
"""
    },
    "components": {
        "__init__.py": "",
        "kpi_card.py": """
from typing import Callable
from datetime import datetime, date
import rio
from utils.models import KPI, KPIType
from utils.styles import *

class KPICard(rio.Component):
    kpi: KPI
    on_submit: Callable[[KPI], None]

    current_value: str = ""
    is_justifying: bool = False
    is_locked: bool = False
    temp_justification: str = ""
    temp_countermeasure: str = ""
    temp_date: str = ""
    temp_resp: str = ""

    def __post_init__(self):
        self.current_value = self.kpi.curr_value
        self.temp_justification = self.kpi.justification
        self.temp_countermeasure = self.kpi.countermeasure
        self.temp_resp = self.kpi.countermeasure_resp
        self.temp_date = self.kpi.countermeasure_date

        if not self.temp_date or not self.temp_date.strip() or self.temp_date == "-":
            self.temp_date = str(date.today())

        if self.kpi.curr_value and str(self.kpi.curr_value).strip() != "":
            self.is_locked = True

    def _clean_float(self, val: str) -> float:
        try:
            clean = str(val).replace("%", "").strip().replace(",", "").replace("_", "")
            if not clean: return 0.0
            return float(clean)
        except: return 0.0

    def _is_performance_bad(self, value: str, target: str) -> bool:
        if not value or not str(value).strip(): return False 
        try:
            type_str = str(self.kpi.type.value if isinstance(self.kpi.type, KPIType) else self.kpi.type).upper()
            if "TEXT" in type_str:
                return str(value).strip().lower() != str(target).strip().lower()
            val_f = self._clean_float(value)
            tgt_f = self._clean_float(target)
            if "LOWER" in type_str: return val_f > tgt_f
            else: return val_f < tgt_f
        except: return True 

    def _calculate_state(self) -> tuple[str, rio.Color, bool]:
        if self.is_locked: return ("SAVED", COLOR_LOCKED, False)
        if not self.current_value.strip(): return ("SEND", COLOR_DISABLED, False)
        is_bad = self._is_performance_bad(self.current_value, self.kpi.curr_target)
        return ("JUSTIFY", COLOR_RED, True) if is_bad else ("SEND", COLOR_GREEN, True)

    def _get_value_color(self) -> rio.Color:
        if not self.current_value: return COLOR_GREY_TXT
        is_bad = self._is_performance_bad(self.current_value, self.kpi.curr_target)
        return COLOR_RED if is_bad else COLOR_GREEN

    def _on_change(self, event):
        if not self.is_locked:
            self.current_value = event.text
            self.kpi.curr_value = event.text

    def _on_main_button_click(self):
        if self.is_locked: return
        lbl, _, _ = self._calculate_state()
        if lbl == "JUSTIFY": self.is_justifying = True
        else:
            self.on_submit(self.kpi)
            self.is_locked = True 

    def _on_save_justification(self):
        self.kpi.justification = self.temp_justification
        self.kpi.countermeasure = self.temp_countermeasure
        self.kpi.countermeasure_date = self.temp_date
        self.kpi.countermeasure_resp = self.temp_resp
        self.is_justifying = False
        self.on_submit(self.kpi)
        self.is_locked = True

    def _build_spec_block(self, label: str, value: str, custom_color: rio.Color = None, is_bold: bool = False):
        final_color = custom_color if custom_color else COLOR_GREY_TXT
        display_val = str(value)
        if "nan" in display_val.lower() or display_val.strip() == "":
            display_val = "-"
            final_color = COLOR_DISABLED
        return rio.Column(
            rio.Text(label.upper(), style=BODY_STYLE.replace(font_size=0.65, fill=rio.Color.from_hex("#6B7280"), font_weight="bold"), justify="center"),
            rio.Text(display_val, style=BODY_STYLE.replace(font_size=1.3, fill=final_color, font_weight="bold" if is_bold else "normal"), justify="center"),
            spacing=0.3, min_width=7, align_x=0.5
        )

    def _build_actual_input_or_view(self):
        if self.is_locked:
            return rio.Column(
                rio.Text("ACTUAL", style=BODY_STYLE.replace(font_size=0.65, font_weight="bold", fill=rio.Color.from_hex("#111827")), justify="center"),
                rio.Text(self.current_value, style=BODY_STYLE.replace(font_size=1.3, fill=self._get_value_color(), font_weight="bold"), justify="center"),
                spacing=0.3, align_x=0.5, min_width=7
            )
        else:
            return rio.Column(
                rio.Text("ACTUAL", style=BODY_STYLE.replace(font_size=0.65, font_weight="bold", fill=rio.Color.from_hex("#111827")), justify="center"),
                rio.TextInput(text=self.current_value, on_change=self._on_change, label="", min_width=7),
                spacing=0.3, align_x=0.5
            )

    def _get_date_value(self) -> date:
        try:
            return date.fromisoformat(self.temp_date)
        except (ValueError, TypeError):
            try:
                return datetime.strptime(self.temp_date, "%Y-%m-%d").date()
            except:
                return date.today()

    def _build_metrics_view(self):
        lbl, btn_color, enabled = self._calculate_state()
        try:
            prev_bad = self._is_performance_bad(self.kpi.prev_achieved, self.kpi.prev_target)
            prev_color = COLOR_RED if prev_bad else COLOR_GREEN
        except: prev_color = COLOR_GREY_TXT
        return rio.Row(
            self._build_spec_block("Prev Target", self.kpi.prev_target),
            self._build_spec_block("Prev Achieved", self.kpi.prev_achieved, custom_color=prev_color, is_bold=True),
            rio.Rectangle(fill=rio.Color.from_hex("#E5E7EB"), min_width=0.1, min_height=3, margin_x=2),
            self._build_spec_block("Target", self.kpi.curr_target, custom_color=rio.Color.from_hex("#111827"), is_bold=True),
            self._build_actual_input_or_view(),
            rio.Column(rio.Spacer(min_height=1.8), rio.Button(lbl, on_press=self._on_main_button_click, color=btn_color, min_width=8, is_sensitive=enabled), spacing=0.3),
            spacing=1.5, align_y=0.5, min_width=50
        )

    def _build_justification_form(self):
        return rio.Card(
            rio.Row(
                rio.Column(
                    rio.Row(rio.Icon("material/info", fill=COLOR_RED, min_width=1.2, min_height=1.2), rio.Text("ACTION REQUIRED", style=rio.TextStyle(font_size=0.6, font_weight="bold", fill=COLOR_RED)), spacing=0.5, align_y=0.5),
                    rio.Text(f"Result '{self.current_value}' < Target '{self.kpi.curr_target}'. Please justify.", style=rio.TextStyle(font_size=0.8, fill=rio.Color.from_hex("#D4D4D8")), overflow="wrap"),
                    spacing=0.5, min_width=15, margin_right=1
                ),
                rio.MultiLineTextInput(text=self.temp_justification, on_change=lambda e: setattr(self, 'temp_justification', e.text), label="Root Cause", min_height=6, grow_x=True),
                rio.MultiLineTextInput(text=self.temp_countermeasure, on_change=lambda e: setattr(self, 'temp_countermeasure', e.text), label="Countermeasure", min_height=6, grow_x=True),
                rio.Column(
                    rio.DateInput(value=self._get_date_value(), on_change=lambda event: setattr(self, 'temp_date', str(event.value)), label="Due Date", min_width=10),
                    rio.TextInput(text=self.temp_resp, on_change=lambda e: setattr(self, 'temp_resp', e.text), label="Responsible", min_width=10),
                    rio.Row(rio.Button("SAVE", on_press=self._on_save_justification, color=rio.Color.from_hex("#FFFFFF"), min_width=5), rio.Button("CANCEL", on_press=lambda: setattr(self, 'is_justifying', False), color=rio.Color.from_hex("#27272A"), min_width=5), spacing=0.5, align_x=1),
                    spacing=0.5, min_width=12
                ),
                spacing=1.5, align_y=0, margin=1
            ),
            color=rio.Color.from_hex("#18181B"), corner_radius=0.2, grow_x=True
        )

    def build(self) -> rio.Component:
        right_content = self._build_justification_form() if self.is_justifying else self._build_metrics_view()
        return rio.Column(
            rio.Row(
                rio.Column(rio.Text(self.kpi.name, style=TITLE_STYLE.replace(font_size=1.5)), rio.Text(self.kpi.description, style=BODY_STYLE.replace(font_size=0.8), overflow="wrap"), spacing=0.5, grow_x=True, margin_right=3),
                right_content, spacing=0, align_y=0
            ),
            rio.Rectangle(fill=rio.Color.from_hex("#E5E7EB"), min_height=0.1, grow_x=True, margin_y=2.5)
        )
""",
        "historic_cell.py": """
import rio
from utils.models import KPIType
from utils.styles import *

class HistoricMonthCell(rio.Component):
    target: str
    actual: str
    kpi_type: KPIType
    month_name: str

    def _clean_float(self, val: str) -> float:
        try:
            clean = str(val).replace("%", "").strip().replace(",", "").replace("_", "")
            if not clean: return 0.0
            return float(clean)
        except: return 0.0

    def _get_bg_color(self) -> rio.Color:
        if str(self.actual) == "-" or str(self.target) == "-": return BG_NEUTRAL
        try:
            val_f = self._clean_float(self.actual)
            tgt_f = self._clean_float(self.target)
            type_str = str(self.kpi_type.value if isinstance(self.kpi_type, KPIType) else self.kpi_type).upper()
            if "TEXT" in type_str: is_bad = str(self.actual).lower() != str(self.target).lower()
            elif "LOWER" in type_str: is_bad = val_f > tgt_f
            else: is_bad = val_f < tgt_f
            return BG_RED_LIGHT if is_bad else BG_GREEN_LIGHT
        except: return BG_NEUTRAL

    def build(self) -> rio.Component:
        bg = self._get_bg_color()
        if bg == BG_RED_LIGHT: txt_color = rio.Color.from_hex("#991B1B")
        elif bg == BG_GREEN_LIGHT: txt_color = rio.Color.from_hex("#065F46")
        else: txt_color = COLOR_GREY_TXT

        return rio.Rectangle(
            content=rio.Column(
                rio.Text(self.month_name.upper(), style=rio.TextStyle(font_size=0.6, font_weight="bold", fill=rio.Color.from_hex("#9CA3AF"))),
                rio.Text(str(self.actual), style=rio.TextStyle(font_size=1.1, font_weight="bold", fill=txt_color)),
                rio.Text(f"T: {self.target}", style=rio.TextStyle(font_size=0.7, fill=rio.Color.from_hex("#6B7280"))),
                spacing=0.2, align_x=0.5, align_y=0.5
            ),
            fill=bg, corner_radius=0.2, min_width=5.5, min_height=5.5, margin=0.2
        )
""",
        "dashboard_widgets.py": """
import rio
from typing import List, Dict, Any
from utils.styles import *

class SummaryCard(rio.Component):
    title: str
    value: str
    icon: str
    color: rio.Color
    sub_title: str = ""

    def build(self) -> rio.Component:
        return rio.Card(
            content=rio.Column(
                rio.Row(rio.Text(self.title.upper(), style=rio.TextStyle(font_size=0.7, fill=rio.Color.from_hex("#9CA3AF"), font_weight="bold")), rio.Spacer(), rio.Icon(self.icon, fill=self.color)),
                rio.Spacer(height=0.8),
                rio.Text(self.value, style=rio.TextStyle(font_size=2.5, font_weight="bold", fill=self.color)),
                rio.Text(self.sub_title, style=BODY_STYLE.replace(font_size=0.8, fill=rio.Color.from_hex("#6B7280"))),
                spacing=0.5
            ),
            corner_radius=0.3, color=rio.Color.from_hex("#FFFFFF"), min_width=20, grow_x=True, margin=0.5
        )

class RankedKPIList(rio.Component):
    title: str
    kpis: List[Dict[str, Any]]
    is_top: bool = True

    def build(self) -> rio.Component:
        color = COLOR_GREEN if self.is_top else COLOR_RED
        list_items = []
        for item in self.kpis:
            score_text = f"({item['score'] * 100:.1f}%)"
            list_items.append(rio.Row(rio.Text(item['name'], style=BODY_STYLE.replace(font_size=0.9), grow_x=True), rio.Text(score_text, style=BODY_STYLE.replace(font_size=0.9, fill=color, font_weight="bold")), align_y=0.5, margin_y=0.4))

        if not list_items: list_items.append(rio.Text("No data to display.", style=BODY_STYLE.replace(fill=COLOR_DISABLED)))

        return rio.Card(
            content=rio.Column(
                rio.Text(self.title, style=TITLE_STYLE.replace(font_size=1.2, font_weight="bold", fill=rio.Color.from_hex("#111827"))),
                rio.Rectangle(fill=rio.Color.from_hex("#E5E7EB"), min_height=0.1, margin_y=0.5),
                *list_items, spacing=0
            ),
            corner_radius=0.3, color=rio.Color.from_hex("#FFFFFF"), grow_x=True
        )
"""
    },
    "pages": {
        "__init__.py": "",
        "historic_page.py": """
import rio
from typing import List, Dict, Any
from utils.styles import *
from components.historic_cell import HistoricMonthCell

class HistoricPage(rio.Component):
    selected_sector: str = ""
    data: List[Dict[str, Any]] = None

    def __post_init__(self):
        self.data = []
        if self.selected_sector:
            from backend_modular import backend
            try:
                self.data = backend.load_historic_data(self.selected_sector)
            except Exception as e:
                print(f"Erro Histórico: {e}")

    def _build_info_label(self, label: str, value: str, color: rio.Color = COLOR_GREY_TXT, bold: bool = False):
        return rio.Column(
            rio.Text(label, style=rio.TextStyle(font_size=0.55, fill=rio.Color.from_hex("#9CA3AF"), font_weight="bold")),
            rio.Text(str(value), style=rio.TextStyle(font_size=0.85, fill=color, font_weight="bold" if bold else "normal")),
            spacing=0.1, align_x=0
        )

    def build(self) -> rio.Component:
        if not self.selected_sector:
            return rio.Column(rio.Icon("material/history", min_width=4, min_height=4, fill=rio.Color.from_hex("#D1D5DB")), rio.Text("SELECT A DEPARTMENT", style=TITLE_STYLE.replace(font_size=1.5, fill=rio.Color.from_hex("#9CA3AF"))), spacing=1, align_x=0.5, align_y=0.5, grow_y=True)
        if not self.data: return rio.Column(rio.ProgressCircle(), align_x=0.5, align_y=0.5, grow_y=True)

        rows = []
        for item in self.data:
            name_col = rio.Rectangle(
                content=rio.Row(
                    rio.Column(
                        rio.Text(item['name'], style=rio.TextStyle(font_size=0.85, font_weight="bold", fill=rio.Color.from_hex("#1F2937")), overflow="wrap"),
                        rio.Row(rio.Text("Unit:", style=rio.TextStyle(font_size=0.6, fill=rio.Color.from_hex("#9CA3AF"))), rio.Text(item.get('unit', '-'), style=rio.TextStyle(font_size=0.6, font_weight="bold", fill=rio.Color.from_hex("#6B7280"))), spacing=0.2),
                        spacing=0.3, grow_x=True, align_y=0.5
                    ),
                    rio.Rectangle(fill=rio.Color.from_hex("#F3F4F6"), min_width=0.1, margin_x=0.8),
                    rio.Column(
                        rio.Row(self._build_info_label("YTD 2025", item.get('ytd', '-'), color=rio.Color.from_hex("#111827"), bold=True), self._build_info_label("'24 RESULT", item.get('res_2024', '-')), spacing=1.5),
                        rio.Spacer(min_height=0.3),
                        rio.Row(self._build_info_label("'25 TARGET", item.get('target_2025', '-')), self._build_info_label("'25 CHALLENGE", item.get('challenge_2025', '-'), color=rio.Color.from_hex("#EA580C"), bold=True), spacing=1.5),
                        spacing=0, align_y=0.5
                    ),
                    spacing=0, margin=0.8, align_y=0.5
                ),
                fill=rio.Color.from_hex("#FFFFFF"), min_width=22, min_height=5.5, corner_radius=0.2, margin=0.2
            )
            month_cells = []
            for m_idx in range(1, 13):
                m_data = item['months'][m_idx]
                month_cells.append(HistoricMonthCell(target=m_data['target'], actual=m_data['actual'], kpi_type=item['type'], month_name=m_data['name']))
            rows.append(rio.Row(name_col, rio.ScrollContainer(rio.Row(*month_cells, spacing=0), scroll_x=True, scroll_y=False, grow_x=True), spacing=0.5, margin_y=0.2))

        return rio.ScrollContainer(rio.Column(*rows, spacing=0.5, margin=1), grow_y=True, scroll_y=True)
""",
        "dashboard_page.py": """
import rio
from typing import Optional, Dict, Any, List
from datetime import date
from dateutil.relativedelta import relativedelta
from utils.styles import *
from utils.constants import MONTH_NAMES, MONTH_OPTIONS
from components.dashboard_widgets import SummaryCard, RankedKPIList

class DashboardPage(rio.Component):
    dashboard_data: Optional[Dict[str, Any]] = None
    filter_month_name: str = ""
    filter_sector: str = "ALL DEPARTMENTS"
    available_sectors: List[str] = ["ALL DEPARTMENTS"]

    def __post_init__(self):
        last_month_dt = date.today() - relativedelta(months=1)
        self.filter_month_name = last_month_dt.strftime('%B')
        from backend_modular import backend
        raw = backend.get_available_sectors()
        self.available_sectors = ["ALL DEPARTMENTS"] + raw
        self._recalculate()

    def _recalculate(self):
        target_month_idx = MONTH_OPTIONS.get(self.filter_month_name, 1)
        self.dashboard_data = self._calculate_dashboard_metrics(target_month_idx, self.filter_sector)

    def _on_filter_change(self, event):
        self._recalculate()

    def _is_kpi_bad(self, actual, target, kpi_type) -> bool:
        try:
            def clean_float(val):
                clean = str(val).replace("%", "").strip().replace(",", "").replace("_", "")
                return float(clean) if clean else 0.0

            if kpi_type.value == 'TEXT': return str(actual).lower() != str(target).lower()
            val_f = clean_float(actual)
            tgt_f = clean_float(target)
            if kpi_type.value == 'LOWER_THAN': return val_f > tgt_f
            else: return val_f < tgt_f
        except: return True

    def _calculate_dashboard_metrics(self, month_idx: int, sector_filter: str) -> Optional[Dict[str, Any]]:
        from backend_modular import backend

        all_kpis_data = []
        sectors_to_load = [s for s in self.available_sectors if s != "ALL DEPARTMENTS"] if sector_filter == "ALL DEPARTMENTS" else [sector_filter]

        for sector in sectors_to_load:
            historic_data = backend.load_historic_data(sector)
            all_kpis_data.extend(historic_data)

        if not all_kpis_data: return None

        total_kpis = 0
        kpis_on_target = 0
        kpi_scores = []

        for item in all_kpis_data:
            month_data = item['months'].get(month_idx)
            if not month_data or str(month_data['actual']) == "-" or str(month_data['target']) == "-": continue 

            total_kpis += 1
            is_bad = self._is_kpi_bad(month_data['actual'], month_data['target'], item['type'])
            if not is_bad: kpis_on_target += 1

            score = 0.0
            try:
                val_f = float(str(month_data['actual']).replace('%', '').replace(',',''))
                tgt_f = float(str(month_data['target']).replace('%', '').replace(',',''))
                if tgt_f != 0:
                    if item['type'].value == 'LOWER_THAN': score = (tgt_f / val_f) if val_f > 0 else 0 
                    else: score = val_f / tgt_f
                else: score = 1.0 if not is_bad else 0.0
            except: score = 0.0

            kpi_scores.append({"name": item['name'], "score": score, "status": "Red" if is_bad else "Green"})

        ranked_scores = sorted([s for s in kpi_scores if s['score'] != 0.0], key=lambda x: x['score'], reverse=True)
        top_kpis = ranked_scores[:3]
        bottom_kpis = ranked_scores[-3:]
        if len(ranked_scores) > 3 and ranked_scores[0]['score'] < 1.0: bottom_kpis = ranked_scores

        return {
            "total_kpis": total_kpis, "on_target": kpis_on_target, "needs_action": total_kpis - kpis_on_target,
            "perc_on_target": f"{kpis_on_target / total_kpis * 100:.1f}%" if total_kpis > 0 else "0.0%",
            "top_kpis": top_kpis, "bottom_kpis": bottom_kpis, "display_month": self.filter_month_name
        }

    def build(self) -> rio.Component:
        if self.dashboard_data is None: return rio.Column(rio.ProgressCircle(), rio.Text("Calculating Analytics...", style=BODY_STYLE), align_x=0.5, align_y=0.5, grow_y=True)
        data = self.dashboard_data

        filter_bar = rio.Row(rio.Dropdown(label="Evaluation Month", options=MONTH_NAMES, selected_value=self.filter_month_name, on_change=self._on_filter_change, min_width=15), rio.Dropdown(label="Department Scope", options=self.available_sectors, selected_value=self.filter_sector, on_change=self._on_filter_change, min_width=20), spacing=2.0, margin_bottom=1.5)
        summary_row = rio.Row(SummaryCard(title="TOTAL KPIS", value=str(data['total_kpis']), sub_title="KPIs found", icon="material/data_thresholding", color=rio.Color.from_hex("#111827")), SummaryCard(title="ON TARGET", value=str(data['on_target']), sub_title=f"Achieved ({data['perc_on_target']})", icon="material/check_circle", color=COLOR_GREEN), SummaryCard(title="NEEDS ACTION", value=str(data['needs_action']), sub_title=f"Requires justification", icon="material/warning", color=COLOR_RED), spacing=1.0, margin_x=1)
        ranking_row = rio.Row(RankedKPIList(title="TOP 3 PERFORMERS", kpis=data['top_kpis'], is_top=True), RankedKPIList(title="BOTTOM 3 PERFORMERS", kpis=data['bottom_kpis'], is_top=False), spacing=2.0)
        title_context = rio.Text(f"EXECUTIVE SUMMARY - {data['display_month'].upper()}", style=TITLE_STYLE.replace(font_size=1.5, font_weight="bold"), margin_bottom=0.5)

        return rio.ScrollContainer(rio.Column(rio.Row(title_context, rio.Spacer(), filter_bar, align_y=0.5), summary_row, ranking_row, spacing=1.5, margin=2), grow_y=True)
"""
    },
    ".": {
        "backend.py": """
import io
import os
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
from typing import List, Dict, Any
from utils.models import KPI, KPIType
from utils.constants import MONTH_OPTIONS

class SharePointBackend:
    def __init__(self):
        self.site_url = "https://gwmglobal.sharepoint.com/sites/DataAnalytics"
        self.client_id = "6c81a342-620c-4614-9398-522af668fcdd"
        self.client_secret = "2U18Q~~lQ6V.lpmOocSdU7fKRk2Uq1fX5ouX6chb"
        self.remote_file_url = "Shared Documents/5.Information Registry/VehicleInsert.xlsx"
        self.local_file_name = "KPISystems.xlsx"
        self.df_cache = None

        # Mapeamento do Backend (Mantido igual)
        self.months_map = {
            1: {"target": "1月 Jan.", "suffix": "Jan"}, 2: {"target": "2月 Feb.", "suffix": "Feb"},
            3: {"target": "3月 Mar.", "suffix": "Mar"}, 4: {"target": "4月 Apr.", "suffix": "Apr"},
            5: {"target": "5月 May", "suffix": "May"}, 6: {"target": "6月 Jun.", "suffix": "Jun"},
            7: {"target": "7月 Jul.", "suffix": "Jul"}, 8: {"target": "8月 Aug.", "suffix": "Aug"},
            9: {"target": "9月 Sep.", "suffix": "Sep"}, 10: {"target": "10月 Oct.", "suffix": "Oct"},
            11: {"target": "11月 Nov.", "suffix": "Nov"}, 12: {"target": "12月 Dec.", "suffix": "Dec"},
        }

    def _get_context(self):
        credentials = ClientCredential(self.client_id, self.client_secret)
        return ClientContext(self.site_url).with_credentials(credentials)

    def _calculate_periods(self):
        today = date.today()
        eval_date = today - relativedelta(months=1)
        prev_date = eval_date - relativedelta(months=1)
        return eval_date, prev_date

    def _parse_kpi_type(self, type_str: str) -> KPIType:
        if not isinstance(type_str, str): return KPIType.GREATER_THAN
        clean_str = type_str.strip().upper().replace(" ", "_")
        if "TEXT" in clean_str: return KPIType.TEXT
        if "LOWER" in clean_str: return KPIType.LOWER_THAN
        return KPIType.GREATER_THAN

    def _refresh_cache_if_needed(self):
        if self.df_cache is None:
            if os.path.exists(self.local_file_name):
                print(f"📂 [Backend] Lendo arquivo LOCAL: {self.local_file_name}")
                self.df_cache = pd.read_excel(self.local_file_name, sheet_name=0)
            else:
                print("☁️ [Backend] Baixando do SharePoint...")
                try:
                    ctx = self._get_context()
                    response = io.BytesIO()
                    ctx.web.get_file_by_server_relative_path(self.remote_file_url).download(response).execute_query()
                    response.seek(0)
                    self.df_cache = pd.read_excel(response, sheet_name=0)
                except Exception as e:
                    print(f"❌ [Backend] Erro crítico: {e}")
                    self.df_cache = pd.DataFrame()
            self.df_cache.columns = self.df_cache.columns.str.strip()

    def get_available_sectors(self) -> List[str]:
        self._refresh_cache_if_needed()
        if self.df_cache is None or 'Title' not in self.df_cache.columns: return []
        try:
            sectors = self.df_cache['Title'].dropna().astype(str).str.strip().unique()
            return sorted([s for s in sectors if s])
        except Exception as e: return []

    def load_data(self, sector: str = None) -> List[KPI]:
        self._refresh_cache_if_needed()
        df_view = self.df_cache
        if sector and 'Title' in self.df_cache.columns:
            df_view = self.df_cache[self.df_cache['Title'].fillna('').astype(str).str.strip().str.lower() == sector.strip().lower()]

        eval_date, prev_date = self._calculate_periods()
        curr_info = self.months_map[eval_date.month]
        prev_info = self.months_map[prev_date.month]
        kpi_list = []

        for index, row in df_view.iterrows():
            kpi_type = self._parse_kpi_type(str(row.get('Type') or row.get('type') or 'GREATER THAN'))
            def clean_val(val):
                if pd.isna(val): return ""
                if isinstance(val, (float, int)): return str(int(val)) if float(val).is_integer() else str(val)
                return str(val)

            kpi = KPI(
                id=str(row.get('序号 No.', index)),
                name=str(row.get('指标名称 Indicator name', 'Unnamed KPI')),
                description=str(row.get(' 口径 KPI description') or row.get('口径 KPI description') or ""),
                type=kpi_type,
                prev_target=str(row.get(prev_info['target'], 0)),
                prev_achieved=str(row.get(f"Achieved {prev_info['suffix']}", 0)),
                curr_target=str(row.get(curr_info['target'], 0)),
                curr_value=clean_val(row.get(f"Achieved {curr_info['suffix']}")),
                justification=clean_val(row.get(f"Justification - {curr_info['suffix']}")),
                countermeasure=clean_val(row.get(f"Countermeasure - {curr_info['suffix']}")),
                countermeasure_date=clean_val(row.get(f"Countermeasure Date - {curr_info['suffix']}")),
                countermeasure_resp=clean_val(row.get(f"Responsible - {curr_info['suffix']}"))
            )
            kpi_list.append(kpi)
        return kpi_list

    def load_historic_data(self, sector: str) -> List[Dict[str, Any]]:
        self._refresh_cache_if_needed()
        df_view = self.df_cache
        if sector and 'Title' in self.df_cache.columns:
            df_view = self.df_cache[self.df_cache['Title'].fillna('').astype(str).str.strip().str.lower() == sector.strip().lower()]

        historic_list = []
        def fmt_num(val):
            if pd.isna(val) or str(val).strip() == "": return "-"
            try:
                clean_val = str(val).replace("%", "").replace(",", "").strip()
                f = float(clean_val)
                return str(int(f)) if f.is_integer() else f"{f:.2f}"
            except: return str(val)

        for index, row in df_view.iterrows():
            monthly_data = {}
            ytd_sum = 0.0
            has_ytd = False
            for m_idx in range(1, 13):
                info = self.months_map[m_idx]
                raw_act = row.get(f"Achieved {info['suffix']}")
                try:
                    if pd.notna(raw_act) and str(raw_act).strip() != "":
                        ytd_sum += float(str(raw_act).replace("%", "").replace(",", "").strip())
                        has_ytd = True
                except: pass
                monthly_data[m_idx] = {"name": info['suffix'], "target": fmt_num(row.get(info['target'])), "actual": fmt_num(raw_act)}

            historic_list.append({
                "id": str(row.get('序号 No.', index)),
                "name": str(row.get('指标名称 Indicator name', 'Unnamed KPI')),
                "type": self._parse_kpi_type(str(row.get('Type') or 'GREATER THAN')),
                "unit": str(row.get('单位 Units') or "-"),
                "res_2024": fmt_num(row.get('2024 年度成果  Annual Results 2024')),
                "target_2025": fmt_num(row.get('2025年目标 Basic Target in 2025')),
                "challenge_2025": fmt_num(row.get('2025年目标 ChallengeTarget in 2025')),
                "ytd": fmt_num(ytd_sum) if has_ytd else "-",
                "months": monthly_data
            })
        return historic_list

    def save_kpi(self, kpi: KPI):
        if self.df_cache is None: self._refresh_cache_if_needed()
        eval_date, _ = self._calculate_periods()
        suffix = self.months_map[eval_date.month]["suffix"]
        try:
            mask = self.df_cache['序号 No.'].astype(str) == str(kpi.id)
            if not mask.any(): return
            row_idx = self.df_cache.index[mask].tolist()[0]
            col_achieved = f"Achieved {suffix}"
            self.df_cache.at[row_idx, col_achieved] = kpi.curr_value
            if kpi.justification:
                self.df_cache.at[row_idx, f"Justification - {suffix}"] = kpi.justification
                self.df_cache.at[row_idx, f"Countermeasure - {suffix}"] = kpi.countermeasure
                self.df_cache.at[row_idx, f"Responsible - {suffix}"] = kpi.countermeasure_resp
                self.df_cache.at[row_idx, f"Countermeasure Date - {suffix}"] = kpi.countermeasure_date

            if os.path.exists(self.local_file_name):
                self.df_cache.to_excel(self.local_file_name, index=False)
            else:
                self._upload_to_sharepoint()
        except Exception as e: print(f"Erro ao salvar: {e}")

    def _upload_to_sharepoint(self):
        try:
            ctx = self._get_context()
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer: self.df_cache.to_excel(writer, index=False)
            output.seek(0)
            ctx.web.get_folder_by_server_relative_url("Shared Documents/5.Information Registry").upload_file("VehicleInsert.xlsx", output.read()).execute_query()
        except Exception as e: print(f"Upload falhou: {e}")

backend = SharePointBackend()
""",
        "main.py": """
import rio
from pathlib import Path
from utils.styles import *
from utils.models import KPI
from components.kpi_card import KPICard
from pages.historic_page import HistoricPage
from pages.dashboard_page import DashboardPage

class PerformanceInputPage(rio.Component):
    active_page: str = "insert" 
    menu_open: bool = False
    selected_sector: str = "" 
    kpis: list[KPI] = None
    available_sectors: list[str] = [""] 

    def __post_init__(self):
        self.kpis = []
        from backend_modular import backend
        try:
            raw_sectors = backend.get_available_sectors()
            self.available_sectors = [""] + raw_sectors
        except Exception as e:
            self.available_sectors = [""]

    def _navigate_to(self, page: str):
        self.active_page = page
        self.menu_open = False

    def _load_data(self, sector):
        from backend_modular import backend
        try:
            print(f"🔄 [Front] Solicitando KPIs para: {sector}")
            self.kpis = [] 
            self.kpis = backend.load_data(sector)
        except Exception as e:
            self.kpis = []

    def _handle_save_kpi(self, kpi: KPI):
        from backend_modular import backend
        try:
            backend.save_kpi(kpi)
        except Exception as e:
            print(f"Erro: {e}")

    def _on_sector(self, event):
        new_val = event.value
        self.selected_sector = new_val
        if self.active_page == "insert":
            if new_val and new_val.strip(): self._load_data(new_val)
            else: self.kpis = []

    def _build_menu_item(self, text: str, icon: str, action):
        return rio.Button(
            style="plain-text", on_press=action,
            content=rio.Row(rio.Icon(icon, fill=rio.Color.from_hex("#374151")), rio.Text(text, style=MENU_TEXT_STYLE), spacing=1.5, align_x=0),
            align_x=0, grow_x=True
        )

    def _build_menu_drawer(self):
        if not self.menu_open: return rio.Spacer()
        return rio.Stack(
            rio.PointerEventListener(on_press=lambda event: setattr(self, 'menu_open', False), content=rio.Rectangle(fill=rio.Color.from_hex("#000000").replace(opacity=0.5), grow_x=True, grow_y=True)),
            rio.Rectangle(
                content=rio.Column(
                    rio.Row(rio.Text("MENU", style=TITLE_STYLE.replace(font_size=1.2, font_weight="bold")), rio.Spacer(), rio.Button(rio.Icon("material/close", fill=rio.Color.from_hex("#374151")), style="plain-text", on_press=lambda: setattr(self, 'menu_open', False)), margin_bottom=3),
                    rio.Column(
                        self._build_menu_item("Insert Results", "material/edit_note", lambda: self._navigate_to("insert")),
                        self._build_menu_item("Historic", "material/history", lambda: self._navigate_to("historic")),
                        self._build_menu_item("Dashboard", "material/dashboard", lambda: self._navigate_to("dashboard")),
                        spacing=0.5, align_x=0, grow_x=True
                    ), margin=2, align_y=0, align_x=0
                ), fill=rio.Color.from_hex("#FFFFFF"), min_width=18, align_x=0, grow_y=True
            )
        )

    def _build_insert_content(self):
        if not self.kpis or not self.selected_sector:
            return rio.Column(rio.Icon("material/bar_chart", min_width=4, min_height=4, fill=rio.Color.from_hex("#D1D5DB")), rio.Text("SELECT A DEPARTMENT", style=TITLE_STYLE.replace(font_size=1.5, fill=rio.Color.from_hex("#9CA3AF"))), spacing=1, align_x=0.5, align_y=0.5, min_height=35)
        else:
            return rio.ScrollContainer(rio.Column(*[KPICard(k, on_submit=self._handle_save_kpi, key=f"{self.selected_sector}-{k.id}") for k in self.kpis], spacing=0, margin_x=4, margin_top=3), grow_y=True)

    def build(self) -> rio.Component:
        show_dropdown = self.active_page in ["insert", "historic"]
        header_right = rio.Spacer()
        if show_dropdown:
            header_right = rio.Row(rio.Text("DEPT:", style=BODY_STYLE.replace(font_size=0.7, fill=rio.Color.from_hex("#D1D5DB"), font_weight="600")), rio.Dropdown(options=self.available_sectors, selected_value=self.selected_sector, on_change=self._on_sector, label=""), spacing=0.5, align_y=0.5)

        if self.active_page == "insert":
            body_content = self._build_insert_content()
            title_text = "PERFORMANCE INPUT"
        elif self.active_page == "historic":
            body_content = HistoricPage(selected_sector=self.selected_sector, key=str(self.selected_sector))
            title_text = "HISTORIC DATA"
        else:
            body_content = DashboardPage(key="dashboard-global") 
            title_text = "EXECUTIVE DASHBOARD"
            header_right = rio.Spacer()

        main_ui = rio.Column(
            rio.Rectangle(
                content=rio.Row(
                    rio.Button(content=rio.Icon("material/menu", fill=rio.Color.from_hex("#FFFFFF"), min_width=1.2, min_height=1.2), style="plain-text", on_press=lambda: setattr(self, 'menu_open', True)),
                    rio.Spacer(grow_x=True),
                    rio.Row(rio.Image(Path("wlogo.png"), min_width=2.2, min_height=2.2), rio.Column(rio.Text(title_text, style=TITLE_STYLE.replace(font_size=1.0, fill=rio.Color.from_hex("#FFFFFF"), font_weight="300")), rio.Text("PMO ANALYTICS", style=BODY_STYLE.replace(font_size=0.6, fill=rio.Color.from_hex("#D1D5DB"), font_weight="300")), spacing=0.05, align_y=0.5), spacing=0.8, align_y=0.5),
                    rio.Spacer(grow_x=True),
                    header_right, spacing=2.5, align_y=0.5, margin=1.2
                ), fill=rio.Color.from_hex("#000000"), grow_x=True
            ),
            rio.Rectangle(content=body_content, fill=rio.Color.from_hex("#FFFAFA"), grow_x=True, grow_y=True),
        )
        if self.menu_open: return rio.Stack(main_ui, self._build_menu_drawer())
        else: return main_ui

if __name__ == "__main__":
    app = rio.App(build=PerformanceInputPage, theme=rio.Theme.from_colors(primary_color=rio.Color.from_hex("#36454F"), secondary_color=rio.Color.from_hex("#9CA3AF"), neutral_color=rio.Color.from_hex("#FFFAFA"), mode="light"))
    app.run_in_browser()
"""
    }
}


def create_files(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_files(path, content)
        else:
            print(f"Criando: {path}")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content.strip())


if __name__ == "__main__":
    create_files(".", project_structure)
    print("\\n✅ Estrutura criada com sucesso!")
    print("🚀 Para rodar, use: python -m rio run main.py")