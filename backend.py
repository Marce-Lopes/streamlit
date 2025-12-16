import io
import os
import time
import json
import pandas as pd
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
from typing import List, Dict, Any, Optional
from utils.models import KPI, KPIType
from utils.constants import MONTH_OPTIONS
from pathlib import Path


class SharePointBackend:
    def __init__(self):
        self.site_url = "https://gwmglobal.sharepoint.com/sites/DataAnalytics"
        self.client_id = "6c81a342-620c-4614-9398-522af668fcdd"
        self.client_secret = ${{secrets.sharepoint_secret}}
        self.remote_file_url = "Shared Documents/5.Information Registry/KPISystem.xlsx"
        self.local_file_name = "../KPISystem.xlsx"

        # Cache na memória
        self.df_cache = None

        # Controle de Cache (TTL) - 15 minutos para auto-refresh
        self.last_fetch_time = 0
        self.cache_validity_seconds = 900  # 900 segundos = 15 minutos

        # 🆕 Sistema de Cache Persistente e Fila de Pendências
        self.cache_dir = Path(__file__).parent / ".cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.pending_queue_file = self.cache_dir / "pending_queue.json"
        self.pending_queue = self._load_pending_queue()

        # Mapeamento do Backend
        self.months_map = {
            1: {"target": "1月 Jan.", "suffix": "Jan"}, 2: {"target": "2月 Feb.", "suffix": "Feb"},
            3: {"target": "3月 Mar.", "suffix": "Mar"}, 4: {"target": "4月 Apr.", "suffix": "Apr"},
            5: {"target": "5月 May", "suffix": "May"}, 6: {"target": "6月 Jun.", "suffix": "Jun"},
            7: {"target": "7月 Jul.", "suffix": "Jul"}, 8: {"target": "8月 Aug.", "suffix": "Aug"},
            9: {"target": "9月 Sep.", "suffix": "Sep"}, 10: {"target": "10月 Oct.", "suffix": "Oct"},
            11: {"target": "11月 Nov.", "suffix": "Nov"}, 12: {"target": "12月 Dec.", "suffix": "Dec"},
        }

    def _load_pending_queue(self) -> List[Dict[str, Any]]:
        """Carrega a fila de pendências do disco"""
        if self.pending_queue_file.exists():
            try:
                with open(self.pending_queue_file, 'r', encoding='utf-8') as f:
                    queue = json.load(f)
                    print(f"📥 [Cache] Carregados {len(queue)} itens pendentes")
                    return queue
            except Exception as e:
                print(f"⚠️ [Cache] Erro ao carregar fila: {e}")
        return []

    def _save_pending_queue(self):
        """Salva a fila de pendências no disco"""
        try:
            with open(self.pending_queue_file, 'w', encoding='utf-8') as f:
                json.dump(self.pending_queue, f, indent=2, ensure_ascii=False)
            print(f"💾 [Cache] Fila salva: {len(self.pending_queue)} itens pendentes")
        except Exception as e:
            print(f"❌ [Cache] Erro ao salvar fila: {e}")

    def _add_to_pending_queue(self, kpi: KPI, sector: str):
        """Adiciona um KPI à fila de pendências"""
        eval_date, _ = self._calculate_periods()
        suffix = self.months_map[eval_date.month]["suffix"]
        
        # Cria entrada única por KPI
        pending_item = {
            "sector": sector,
            "kpi_id": kpi.id,
            "kpi_name": kpi.name,
            "timestamp": datetime.now().isoformat(),
            "month_suffix": suffix,
            "data": {
                "curr_value": kpi.curr_value,
                "justification": kpi.justification,
                "countermeasure": kpi.countermeasure,
                "countermeasure_date": kpi.countermeasure_date,
                "countermeasure_resp": kpi.countermeasure_resp
            }
        }
        
        # Remove duplicatas antigas do mesmo KPI
        self.pending_queue = [
            item for item in self.pending_queue 
            if not (item["kpi_id"] == kpi.id and item["sector"] == sector and item["month_suffix"] == suffix)
        ]
        
        # Adiciona novo item
        self.pending_queue.append(pending_item)
        self._save_pending_queue()
        print(f"📝 [Cache] KPI {kpi.id} ({kpi.name}) adicionado à fila")

    def _get_context(self):
        credentials = ClientCredential(self.client_id, self.client_secret)
        return ClientContext(self.site_url).with_credentials(credentials)

    def _calculate_periods(self):
        today = date.today()
        # Regra: Avaliamos sempre o mês anterior
        eval_date = today - relativedelta(months=1)
        prev_date = eval_date - relativedelta(months=1)
        return eval_date, prev_date

    def _parse_kpi_type(self, type_str: str) -> KPIType:
        if not isinstance(type_str, str): return KPIType.GREATER_THAN
        clean_str = type_str.strip().upper().replace(" ", "_")
        if "TEXT" in clean_str: return KPIType.TEXT
        if "LOWER" in clean_str: return KPIType.LOWER_THAN
        return KPIType.GREATER_THAN

    def _refresh_cache_if_needed(self, force=False):
        """
        Lógica inteligente de cache:
        1. Se não tem cache (primeira execução) -> Baixa
        2. Se o cache venceu (passou 15 min) -> Baixa
        3. Se force=True (botão clicado) -> Baixa
        4. Após baixar, processa fila de pendências
        5. Faz merge inteligente (SharePoint = verdade, cache preenche vazios)
        """
        current_time = time.time()
        is_expired = (current_time - self.last_fetch_time) > self.cache_validity_seconds

        if self.df_cache is None or is_expired or force:
            trigger = "Forçado" if force else ("Expirado" if is_expired else "Inicial")
            print(f"🔄 [Backend] Atualizando dados ({trigger})...")

            # Prioridade 1: SharePoint sempre (verdade universal)
            # Prioridade 2: Se falhar, arquivo local
            try:
                self._download_from_sharepoint()
            except Exception as e:
                print(f"⚠️ [Backend] SharePoint falhou, tentando arquivo local: {e}")
                if os.path.exists(self.local_file_name):
                    print(f"📂 [Backend] Lendo arquivo LOCAL: {self.local_file_name}")
                    self.df_cache = pd.read_excel(self.local_file_name, sheet_name=0)
                else:
                    print(f"❌ [Backend] Nenhuma fonte disponível!")
                    self.df_cache = pd.DataFrame()

            # Limpeza básica de colunas
            if self.df_cache is not None:
                self.df_cache.columns = self.df_cache.columns.str.strip()
                
                # 🆕 Processa fila de pendências após baixar dados frescos
                self._process_pending_queue()

            # Atualiza o timestamp
            self.last_fetch_time = time.time()

    def _process_pending_queue(self):
        """
        Processa a fila de pendências com lógica de merge inteligente:
        - SharePoint sempre prevalece se tiver valor
        - Cache preenche apenas se SharePoint estiver vazio
        - Remove da fila itens processados com sucesso
        """
        if not self.pending_queue:
            return
        
        print(f"🔄 [Cache] Processando {len(self.pending_queue)} itens pendentes...")
        items_processed = []
        
        for item in self.pending_queue:
            try:
                sector = item["sector"]
                kpi_id = item["kpi_id"]
                suffix = item["month_suffix"]
                data = item["data"]
                
                # Encontra a linha no DataFrame
                mask = (
                    (self.df_cache['Title'].fillna('').astype(str).str.strip().str.lower() == sector.strip().lower()) &
                    (self.df_cache['序号 No.'].astype(str) == str(kpi_id))
                )
                
                if not mask.any():
                    print(f"⚠️ [Cache] KPI {kpi_id} não encontrado no SharePoint")
                    continue
                
                row_idx = self.df_cache.index[mask].tolist()[0]
                col_achieved = f"Achieved {suffix}"
                
                # 🎯 LÓGICA DE MERGE: SharePoint prevalece, cache só preenche vazios
                sp_value = self.df_cache.at[row_idx, col_achieved]
                sp_has_value = pd.notna(sp_value) and str(sp_value).strip() != ""
                
                if sp_has_value:
                    # SharePoint já tem valor → remove da fila (SharePoint prevaleceu)
                    print(f"✅ [Cache] KPI {kpi_id}: SharePoint prevaleceu (valor={sp_value})")
                    items_processed.append(item)
                else:
                    # SharePoint vazio → tenta preencher com cache
                    cache_value = data.get("curr_value", "")
                    if cache_value and str(cache_value).strip():
                        print(f"📝 [Cache] KPI {kpi_id}: Aplicando cache (valor={cache_value})")
                        self.df_cache.at[row_idx, col_achieved] = cache_value
                        
                        # Adiciona justificativas se existirem
                        if data.get("justification"):
                            self.df_cache.at[row_idx, f"Justification - {suffix}"] = data["justification"]
                            self.df_cache.at[row_idx, f"Countermeasure - {suffix}"] = data["countermeasure"]
                            self.df_cache.at[row_idx, f"Responsible - {suffix}"] = data["countermeasure_resp"]
                            self.df_cache.at[row_idx, f"Countermeasure Date - {suffix}"] = data["countermeasure_date"]
                        
                        # Marca para remoção (será processado no próximo save/upload)
                        items_processed.append(item)
                    else:
                        print(f"⚠️ [Cache] KPI {kpi_id}: Cache vazio, mantendo na fila")
                        
            except Exception as e:
                print(f"❌ [Cache] Erro processando KPI {item.get('kpi_id')}: {e}")
        
        # Remove itens processados da fila
        if items_processed:
            self.pending_queue = [item for item in self.pending_queue if item not in items_processed]
            self._save_pending_queue()
            print(f"✨ [Cache] {len(items_processed)} itens processados e removidos da fila")

    def _download_from_sharepoint(self):
        print("☁️ [Backend] Baixando do SharePoint...")
        try:
            ctx = self._get_context()
            response = io.BytesIO()
            ctx.web.get_file_by_server_relative_path(self.remote_file_url).download(response).execute_query()
            response.seek(0)
            self.df_cache = pd.read_excel(response, sheet_name="Sheet1")
            print("✅ [Backend] Download do SharePoint concluído!")
        except Exception as e:
            print(f"❌ [Backend] Erro crítico no download: {e}")
            raise  # Re-lança exceção para fallback funcionar

    def force_refresh_from_sharepoint(self) -> bool:
        """
        Força atualização dos dados do SharePoint (botão manual).
        Retorna True se sucesso, False se falhar.
        """
        print("🔄 [Backend] Refresh manual solicitado...")
        try:
            self._refresh_cache_if_needed(force=True)
            print(f"✅ [Backend] Dados atualizados! Fila: {len(self.pending_queue)} pendentes")
            return True
        except Exception as e:
            print(f"❌ [Backend] Erro no refresh: {e}")
            return False

    def get_pending_count(self) -> int:
        """Retorna quantidade de itens na fila de pendências"""
        return len(self.pending_queue)

    def get_available_sectors(self, force_refresh=False) -> List[str]:
        self._refresh_cache_if_needed(force=force_refresh)
        if self.df_cache is None or 'Title' not in self.df_cache.columns: return []
        try:
            sectors = self.df_cache['Title'].dropna().astype(str).str.strip().unique()
            return sorted([s for s in sectors if s])
        except Exception as e:
            return []

    def load_data(self, sector: str = None, force_refresh=False) -> List[KPI]:
        self._refresh_cache_if_needed(force=force_refresh)
        df_view = self.df_cache
        if sector and 'Title' in self.df_cache.columns:
            df_view = self.df_cache[
                self.df_cache['Title'].fillna('').astype(str).str.strip().str.lower() == sector.strip().lower()]

        print(f"🔍 Setor: {sector}, Linhas encontradas: {len(df_view)}")
        eval_date, prev_date = self._calculate_periods()
        curr_info = self.months_map[eval_date.month]
        prev_info = self.months_map[prev_date.month]
        kpi_list = []

        print(f"⏳ Iniciando processamento de {len(df_view)} linhas...")
        for idx_count, (index, row) in enumerate(df_view.iterrows()):
            if idx_count % 10 == 0:  # Log a cada 10 linhas
                print(f"📊 Processando linha {idx_count}/{len(df_view)}...")
            kpi_type = self._parse_kpi_type(str(row.get('Type') or row.get('type') or 'GREATER THAN'))

            def clean_val(val):
                try:
                    if pd.isna(val): return ""
                    if isinstance(val, (float, int)): return str(int(val)) if float(val).is_integer() else str(val)
                    return str(val)
                except Exception as e:
                    print(f"⚠️ Erro ao limpar valor: {val} - {e}")
                    return ""

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
        
        print(f"✅ Processamento concluído! {len(kpi_list)} KPIs carregados para '{sector}'")
        return kpi_list

    def load_historic_data(self, sector: str, force_refresh=False) -> List[Dict[str, Any]]:
        self._refresh_cache_if_needed(force=force_refresh)
        df_view = self.df_cache
        if sector and 'Title' in self.df_cache.columns:
            df_view = self.df_cache[
                self.df_cache['Title'].fillna('').astype(str).str.strip().str.lower() == sector.strip().lower()]

        historic_list = []

        def fmt_num(val):
            if pd.isna(val) or str(val).strip() == "": return "-"
            try:
                clean_val = str(val).replace("%", "").replace(",", "").strip()
                f = float(clean_val)
                return str(int(f)) if f.is_integer() else f"{f:.2f}"
            except:
                return str(val)

        for index, row in df_view.iterrows():
            monthly_data = {}
            ytd_sum = 0.0
            has_ytd = False
            for m_idx in range(1, 13):
                info = self.months_map[m_idx]
                raw_act = row.get(f"Achieved {info['suffix']}")
                try:
                    if pd.notna(raw_act) and str(raw_act).strip() != "":
                        val_float = float(str(raw_act).replace("%", "").replace(",", "").strip())
                        ytd_sum += val_float
                        has_ytd = True
                except:
                    pass
                monthly_data[m_idx] = {"name": info['suffix'], "target": fmt_num(row.get(info['target'])),
                                       "actual": fmt_num(raw_act)}

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

    def save_kpi(self, kpi: KPI, sector: str = None):
        """
        Salva KPI com sistema inteligente de fila:
        1. Adiciona à fila de pendências (segurança)
        2. Atualiza cache em memória
        3. Salva localmente
        4. Tenta subir para SharePoint
        5. Se falhar, mantém na fila para próxima tentativa
        """
        # Garante que temos dados carregados antes de tentar salvar
        if self.df_cache is None: 
            self._refresh_cache_if_needed()

        eval_date, _ = self._calculate_periods()
        suffix = self.months_map[eval_date.month]["suffix"]

        # 🆕 Passo 0: Adiciona à fila de pendências PRIMEIRO (segurança)
        if sector:
            self._add_to_pending_queue(kpi, sector)

        try:
            # Encontra a linha correta
            mask = self.df_cache['序号 No.'].astype(str) == str(kpi.id)
            if not mask.any():
                print(f"❌ [Backend] KPI ID {kpi.id} não encontrado no cache.")
                print(f"💾 [Backend] Dados salvos na fila de pendências")
                return

            row_idx = self.df_cache.index[mask].tolist()[0]

            # Atualiza o DataFrame em memória
            col_achieved = f"Achieved {suffix}"
            self.df_cache.at[row_idx, col_achieved] = kpi.curr_value

            if kpi.justification:
                self.df_cache.at[row_idx, f"Justification - {suffix}"] = kpi.justification
                self.df_cache.at[row_idx, f"Countermeasure - {suffix}"] = kpi.countermeasure
                self.df_cache.at[row_idx, f"Responsible - {suffix}"] = kpi.countermeasure_resp
                self.df_cache.at[row_idx, f"Countermeasure Date - {suffix}"] = kpi.countermeasure_date

            # Passo 1: Salva Localmente (Segurança Imediata)
            print("💾 [Backend] Salvando localmente...")
            self.df_cache.to_excel(self.local_file_name, index=False)

            # Passo 2: Tenta subir para o SharePoint
            upload_success = self._upload_with_retry()
            
            if upload_success and sector:
                # Upload bem-sucedido → remove da fila
                self.pending_queue = [
                    item for item in self.pending_queue 
                    if not (item["kpi_id"] == kpi.id and item["sector"] == sector and item["month_suffix"] == suffix)
                ]
                self._save_pending_queue()
                print(f"✅ [Backend] KPI {kpi.id} salvo e removido da fila")
            elif not upload_success:
                print(f"⚠️ [Backend] Upload falhou, KPI {kpi.id} mantido na fila")

            # Atualiza timestamp apenas se upload teve sucesso
            if upload_success:
                self.last_fetch_time = time.time()

        except Exception as e:
            print(f"❌ [Backend] Erro geral ao salvar: {e}")
            print(f"💾 [Backend] Dados mantidos na fila de pendências")

    def _upload_with_retry(self, max_retries=3) -> bool:
        """
        Tenta fazer upload. Se o arquivo estiver travado (Lock), espera e tenta de novo.
        Retorna True se sucesso, False se falhar.
        """
        for attempt in range(1, max_retries + 1):
            try:
                print(f"☁️ [Backend] Tentativa de upload {attempt}/{max_retries}...")
                self._upload_to_sharepoint()
                print("✅ [Backend] Upload concluído com sucesso!")
                return True  # Sucesso
            except Exception as e:
                error_msg = str(e).lower()
                is_lock_error = any(keyword in error_msg for keyword in ['lock', 'locked', 'checked out', 'in use'])
                
                if is_lock_error:
                    print(f"🔒 [Backend] Arquivo travado por outro usuário (Admin editando?)")
                else:
                    print(f"⚠️ [Backend] Falha no upload (Tentativa {attempt}): {e}")
                
                if attempt < max_retries:
                    sleep_time = 2 * attempt  # Backoff: espera 2s, depois 4s...
                    print(f"⏳ [Backend] Aguardando {sleep_time} segundos para tentar novamente...")
                    time.sleep(sleep_time)
                else:
                    print("❌ [Backend] Upload falhou após todas as tentativas.")
                    print("💾 [Backend] Arquivo LOCAL atualizado + dados na fila de pendências")
                    return False  # Falha

    def _upload_to_sharepoint(self):
        # Esta função lança exceção se falhar, permitindo que o retry capture
        ctx = self._get_context()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            self.df_cache.to_excel(writer, index=False)
        output.seek(0)

        # Sobrescreve o arquivo no SharePoint
        ctx.web.get_folder_by_server_relative_url("Shared Documents/5.Information Registry") \
            .upload_file("KPISystem.xlsx", output.read()) \
            .execute_query()



backend = SharePointBackend()
