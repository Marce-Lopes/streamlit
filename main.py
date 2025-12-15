import rio
from pathlib import Path
from utils.styles import *
from utils.models import KPI
from components.kpi_card import KPICard
from pages.historic_page import HistoricPage
from pages.dashboard_page import DashboardPage

# Caminho para os assets (logo)
ASSETS_DIR = Path(__file__).parent

class PerformanceInputPage(rio.Component):
    active_page: str = "insert" 
    menu_open: bool = False
    selected_sector: str = "" 
    kpis: list[KPI] = None
    available_sectors: list[str] = [""] 
    pending_count: int = 0  # 🆕 Contador de pendências
    last_refresh: str = ""  # 🆕 Última atualização

    def __post_init__(self):
        self.kpis = []
        logo_path = ASSETS_DIR / "wlogo.png"
        print(f"🖼️ [Logo] Caminho: {logo_path}")
        print(f"🖼️ [Logo] Existe? {logo_path.exists()}")
        from backend import backend
        try:
            raw_sectors = backend.get_available_sectors()
            self.available_sectors = [""] + raw_sectors
            self.pending_count = backend.get_pending_count()
            import datetime
            self.last_refresh = datetime.datetime.now().strftime("%H:%M")
        except Exception as e:
            self.available_sectors = [""]
        
        # 🆕 Inicia auto-refresh a cada 15 minutos
        self._schedule_auto_refresh()

    def _navigate_to(self, page: str):
        self.active_page = page
        self.menu_open = False

    def _schedule_auto_refresh(self):
        """Agenda auto-refresh a cada 15 minutos"""
        async def auto_refresh_loop():
            import asyncio
            while True:
                await asyncio.sleep(900)  # 900 segundos = 15 minutos
                print("⏰ [Auto-Refresh] Executando refresh automático...")
                await self._manual_refresh()
        
        # Inicia a task em background
        self.session.create_task(auto_refresh_loop())
        print("⏰ [Auto-Refresh] Agendado para cada 15 minutos")

    async def _manual_refresh(self):
        """Executa refresh manual dos dados do SharePoint"""
        from backend import backend
        import datetime
        
        print("🔄 [Refresh] Iniciando refresh manual...")
        self.menu_open = False  # Fecha o menu
        
        try:
            success = backend.force_refresh_from_sharepoint()
            self.pending_count = backend.get_pending_count()
            self.last_refresh = datetime.datetime.now().strftime("%H:%M")
            
            # Se estiver na página insert com setor selecionado, recarrega KPIs
            if self.active_page == "insert" and self.selected_sector and self.selected_sector.strip():
                await self._load_data(self.selected_sector)
            
            await self.force_refresh()
            
            if success:
                print(f"✅ [Refresh] Dados atualizados! Pendências: {self.pending_count}")
            else:
                print("⚠️ [Refresh] Refresh falhou, usando cache local")
                
        except Exception as e:
            print(f"❌ [Refresh] Erro: {e}")

    async def _load_data(self, sector):
        from backend import backend
        try:
            print(f"🔄 [Fr] Solicitando KPIs para: {sector}")
            self.kpis = [] 
            print(f"🔃 [Fr] Forçando refresh para limpar KPIs...")
            await self.force_refresh()  # Força render do placeholder
            self.kpis = backend.load_data(sector)
            print(f"✅ [Fr] Recebidos {len(self.kpis)} KPIs no frontend")
            if self.kpis:
                print(f"📝 [Fr] Primeiro KPI: {self.kpis[0].name}")
                # Verifica IDs duplicados
                ids = [k.id for k in self.kpis]
                duplicates = [id_val for id_val in ids if ids.count(id_val) > 1]
                if duplicates:
                    print(f"⚠️ [Fr] ATENÇÃO: IDs duplicados encontrados: {set(duplicates)}")
                    for kpi in self.kpis:
                        if kpi.id in duplicates:
                            print(f"   - ID {kpi.id}: {kpi.name}")
            print(f"🔃 [Fr] Forçando refresh para exibir {len(self.kpis)} KPIs...")
            await self.force_refresh()  # Força render dos KPIs
            print(f"✨ [Fr] Refresh concluído!")
        except Exception as e:
            print(f"❌ [Fr] Erro ao carregar dados: {e}")
            self.kpis = []
            await self.force_refresh()

    def _handle_save_kpi(self, kpi: KPI):
        from backend import backend
        try:
            # 🆕 Passa o setor para o backend (necessário para fila de pendências)
            backend.save_kpi(kpi, sector=self.selected_sector)
        except Exception as e:
            print(f"Erro: {e}")

    async def _on_sector(self, event):
        new_val = event.value
        self.selected_sector = new_val
        if self.active_page == "insert":
            if new_val and new_val.strip(): 
                await self._load_data(new_val)
            else: 
                self.kpis = []
                await self.force_refresh()

    def _build_menu_item(self, text: str, icon: str, action):
        return rio.Button(
            style="plain-text", on_press=action,
            content=rio.Row(rio.Icon(icon, fill=rio.Color.from_hex("#374151")), rio.Text(text, style=MENU_TEXT_STYLE), spacing=1.5, align_x=0),
            align_x=0, grow_x=True
        )

    def _build_menu_drawer(self):
        if not self.menu_open: return rio.Spacer()
        
        # 🆕 Informações de status
        status_info = rio.Column(
            rio.Rectangle(fill=rio.Color.from_hex("#E5E7EB"), min_height=0.1, grow_x=True, margin_y=1.5),
            rio.Text("SYSTEM STATUS", style=BODY_STYLE.replace(font_size=0.7, font_weight="bold", fill=rio.Color.from_hex("#6B7280"))),
            rio.Row(
                rio.Icon("material/schedule", fill=rio.Color.from_hex("#6B7280"), min_width=0.8, min_height=0.8),
                rio.Text(f"Last refresh: {self.last_refresh}", style=BODY_STYLE.replace(font_size=0.7, fill=rio.Color.from_hex("#374151"))),
                spacing=0.5, align_y=0.5
            ),
            rio.Row(
                rio.Icon("material/pending_actions" if self.pending_count > 0 else "material/check_circle", 
                        fill=rio.Color.from_hex("#F59E0B") if self.pending_count > 0 else rio.Color.from_hex("#10B981"), 
                        min_width=0.8, min_height=0.8),
                rio.Text(f"Pending: {self.pending_count}", style=BODY_STYLE.replace(font_size=0.7, fill=rio.Color.from_hex("#374151"))),
                spacing=0.5, align_y=0.5
            ),
            spacing=0.3, align_x=0, margin_top=1
        )
        
        return rio.Stack(
            rio.PointerEventListener(on_press=lambda event: setattr(self, 'menu_open', False), content=rio.Rectangle(fill=rio.Color.from_hex("#000000").replace(opacity=0.5), grow_x=True, grow_y=True)),
            rio.Rectangle(
                content=rio.Column(
                    rio.Row(rio.Text("MENU", style=TITLE_STYLE.replace(font_size=1.2, font_weight="bold")), rio.Spacer(), rio.Button(rio.Icon("material/close", fill=rio.Color.from_hex("#374151")), style="plain-text", on_press=lambda: setattr(self, 'menu_open', False)), margin_bottom=3),
                    rio.Column(
                        self._build_menu_item("Insert Results", "material/edit_note", lambda: self._navigate_to("insert")),
                        self._build_menu_item("Historic", "material/history", lambda: self._navigate_to("historic")),
                        self._build_menu_item("Dashboard", "material/dashboard", lambda: self._navigate_to("dashboard")),
                        rio.Rectangle(fill=rio.Color.from_hex("#E5E7EB"), min_height=0.1, grow_x=True, margin_y=1),
                        self._build_menu_item("🔄 Refresh Data", "material/refresh", self._manual_refresh),
                        spacing=0.5, align_x=0, grow_x=True
                    ),
                    status_info,
                    margin=2, align_y=0, align_x=0
                ), fill=rio.Color.from_hex("#FFFFFF"), min_width=18, align_x=0, grow_y=True
            )
        )

    def _build_insert_content(self):
        if not self.kpis or not self.selected_sector:
            print(f"ℹ️ [Fr] Exibindo placeholder (kpis={len(self.kpis) if self.kpis else 0}, sector='{self.selected_sector}')")
            return rio.Column(rio.Icon("material/bar_chart", min_width=4, min_height=4, fill=rio.Color.from_hex("#D1D5DB")), rio.Text("SELECT A DEPARTMENT", style=TITLE_STYLE.replace(font_size=1.5, fill=rio.Color.from_hex("#9CA3AF"))), spacing=1, align_x=0.5, align_y=0.5, min_height=35)
        else:
            print(f"🎨 [Fr] Renderizando {len(self.kpis)} KPIs para '{self.selected_sector}'")
            try:
                cards = [KPICard(k, on_submit=self._handle_save_kpi, key=f"{self.selected_sector}-{idx}-{k.id}") for idx, k in enumerate(self.kpis)]
                print(f"✅ [Fr] {len(cards)} cards criados com sucesso")
                return rio.ScrollContainer(rio.Column(*cards, spacing=0, margin_x=4, margin_top=3), grow_y=True)
            except Exception as e:
                print(f"❌ [Fr] Erro ao criar KPICards: {e}")
                import traceback
                traceback.print_exc()
                return rio.Text(f"Erro ao renderizar: {e}", style=BODY_STYLE)

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
                    rio.Row(rio.Image(ASSETS_DIR / "wlogo.png", min_width=2.2, min_height=2.2), rio.Column(rio.Text(title_text, style=TITLE_STYLE.replace(font_size=1.0, fill=rio.Color.from_hex("#FFFFFF"), font_weight="300")), rio.Text("PMO ANALYTICS", style=BODY_STYLE.replace(font_size=0.6, fill=rio.Color.from_hex("#D1D5DB"), font_weight="300")), spacing=0.05, align_y=0.5), spacing=0.8, align_y=0.5),
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