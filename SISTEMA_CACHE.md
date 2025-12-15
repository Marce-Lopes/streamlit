# 🔄 Sistema de Cache Inteligente e Fila de Pendências

## 📋 Visão Geral

Sistema robusto que gerencia conflitos entre múltiplos usuários e permite operação 24/7 sem perda de dados.

## 🎯 Funcionalidades

### 1. **Cache Persistente** 
- Todos os dados são salvos em `.cache/pending_queue.json`
- Garante que NENHUM dado seja perdido, mesmo se SharePoint travar

### 2. **Auto-Refresh** ⏰
- A cada **15 minutos** a aplicação busca dados do SharePoint automaticamente
- Processa fila de pendências e tenta reenviar dados que falharam

### 3. **Refresh Manual** 🔄
- Botão "Refresh Data" no menu lateral
- Permite admin forçar atualização imediata
- Mostra status: última atualização e quantos itens pendentes

### 4. **Merge Inteligente** 🧠

#### Regras de Precedência:
```
┌─────────────────────────────────────────────────────┐
│ SHAREPOINT SEMPRE PREVALECE (Verdade Universal)     │
└─────────────────────────────────────────────────────┘

1. SharePoint tem valor + Cache tem valor diferente:
   → SharePoint prevalece, cache é descartado

2. SharePoint vazio + Cache tem valor:
   → Cache preenche SharePoint na próxima sincronização

3. SharePoint travado (Admin editando):
   → Dados ficam na fila de pendências
   → Próximo refresh tenta novamente
   → Usuário não perde nada!

4. SharePoint teve valor adicionado manualmente (Admin):
   → Remove item da fila (não sobrescreve trabalho do admin)
```

## 🔐 Cenários de Uso

### **Cenário 1: Admin Editando no SharePoint**
1. Admin abre Excel no SharePoint (arquivo fica travado 🔒)
2. User tenta adicionar resultado → **Falha no upload**
3. Sistema salva em:
   - ✅ Cache local (`.cache/pending_queue.json`)
   - ✅ Arquivo local (`KPISystem.xlsx`)
4. Após 15 min ou refresh manual:
   - Sistema detecta que SharePoint foi liberado
   - Reenvia dados automaticamente
   - Remove da fila de pendências

### **Cenário 2: Admin Corrige Valor Manualmente**
1. User adiciona valor "100" via app
2. Upload falha, fica na fila
3. Admin abre SharePoint e corrige para "150"
4. Próximo refresh:
   - Sistema detecta que SharePoint tem "150"
   - **Mantém valor do admin** (150)
   - Remove da fila (conflito resolvido)

### **Cenário 3: Aplicação 24/7**
1. App fica aberta o dia todo
2. A cada 15 min busca dados frescos do SharePoint
3. Qualquer edição manual do admin é refletida
4. Fila processa automaticamente pendências antigas

## 📊 Monitoramento

### Menu Lateral - Status
```
SYSTEM STATUS
─────────────────
⏰ Last refresh: 14:35
✓ Pending: 0        → Tudo sincronizado
⚠ Pending: 3        → 3 itens aguardando upload
```

### Console Logs
```bash
# Sucesso
✅ [Backend] Upload concluído com sucesso!
✅ [Cache] 3 itens processados e removidos da fila

# Lock do SharePoint
🔒 [Backend] Arquivo travado por outro usuário (Admin editando?)
💾 [Backend] Dados mantidos na fila de pendências

# SharePoint Prevaleceu
✅ [Cache] KPI 12: SharePoint prevaleceu (valor=150)
```

## 🛠️ Arquivos do Sistema

```
PMO_Data/
├── .cache/                        ← 🆕 Novo diretório
│   └── pending_queue.json         ← Fila de pendências persistente
├── backend.py                     ← Lógica de cache e merge
├── main.py                        ← UI + auto-refresh
└── ../KPISystem.xlsx              ← Cache local do Excel
```

## ⚙️ Configurações

### Tempo de Auto-Refresh
```python
# backend.py linha 27
self.cache_validity_seconds = 900  # 15 minutos
```

### Tentativas de Upload
```python
# backend.py linha 416
def _upload_with_retry(self, max_retries=3):  # 3 tentativas
```

## 🚨 Importante

1. **Nunca deletar `.cache/`** - Contém dados que ainda não subiram
2. **SharePoint é sempre a verdade** - Sistema nunca sobrescreve edições do admin
3. **Fila é automática** - Usuário não precisa fazer nada especial
4. **IDs únicos são essenciais** - Garanta que cada KPI tem ID único na planilha

## 🎓 Para Desenvolvedores

### Adicionar KPI à Fila
```python
backend.save_kpi(kpi, sector="Commercial")
```

### Forçar Refresh
```python
backend.force_refresh_from_sharepoint()
```

### Verificar Pendências
```python
count = backend.get_pending_count()
print(f"Pendentes: {count}")
```

---

**Sistema desenvolvido para operação 24/7 sem perda de dados** ✨

