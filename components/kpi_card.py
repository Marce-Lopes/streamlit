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
        print(f"🎴 [KPICard] Inicializando card: {self.kpi.name}")
        try:
            self.current_value = self.kpi.curr_value
            self.temp_justification = self.kpi.justification
            self.temp_countermeasure = self.kpi.countermeasure
            self.temp_resp = self.kpi.countermeasure_resp
            self.temp_date = self.kpi.countermeasure_date

            if not self.temp_date or not self.temp_date.strip() or self.temp_date == "-":
                self.temp_date = str(date.today())

            if self.kpi.curr_value and str(self.kpi.curr_value).strip() != "":
                self.is_locked = True
            print(f"✅ [KPICard] Card inicializado: {self.kpi.name}")
        except Exception as e:
            print(f"❌ [KPICard] Erro ao inicializar: {e}")
            import traceback
            traceback.print_exc()

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