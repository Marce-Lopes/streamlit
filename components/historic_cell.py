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