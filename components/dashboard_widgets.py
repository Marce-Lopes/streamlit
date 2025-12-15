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