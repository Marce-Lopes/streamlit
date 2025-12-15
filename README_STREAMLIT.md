# 🚀 PMO Analytics - Streamlit Version

## 📋 Migração Completa do Rio para Streamlit

Sistema completo de gerenciamento de KPIs com **cache inteligente**, **auto-refresh** e **fila de pendências**.

---

## ✅ O que foi migrado:

### **Backend (100% mantido)**
- ✅ `backend.py` - Sem alterações
- ✅ `utils/` - Todos os modelos e constantes mantidos
- ✅ Sistema de cache persistente
- ✅ Fila de pendências (`.cache/pending_queue.json`)
- ✅ Merge inteligente SharePoint + Cache

### **Frontend (100% recriado)**
- ✅ `streamlit_app.py` - App principal com navegação
- ✅ `streamlit_pages/insert_results_page.py` - Inserção de KPIs
- ✅ `streamlit_pages/historic_page.py` - Dados históricos
- ✅ `streamlit_pages/dashboard_page.py` - Dashboard executivo
- ✅ CSS customizado mantendo visual original
- ✅ Auto-refresh a cada 15 minutos

---

## 🎯 Funcionalidades

### 1. **Insert Results** 📝
- Adicionar resultados mensais de KPIs
- Validação automática (verde/vermelho)
- Formulário de justificativa para resultados ruins
- Save automático com sistema de fila

### 2. **Historic** 📜
- Visualização de todos os meses (Janeiro-Dezembro)
- Células coloridas por performance
- YTD 2025, Resultados 2024, Targets 2025
- Scroll horizontal para os 12 meses

### 3. **Dashboard** 📊
- Métricas executivas: Total KPIs, On Target, Needs Action
- Top 3 Performers / Bottom 3 Performers
- Filtros por mês e departamento
- Cálculo automático de scores

### 4. **Sistema de Cache Inteligente** 🔄
- **Auto-refresh a cada 15 minutos**
- Fila de pendências persistente
- SharePoint sempre prevalece
- Detecção de arquivo travado (Admin editando)
- Retry automático com backoff

---

## 🚀 Como Usar

### **1. Instalar Dependências**

```bash
cd PMO_Data
pip install -r requirements_streamlit.txt
```

### **2. Executar Aplicação**

```bash
streamlit run streamlit_app.py
```

Ou use o script Windows:

```powershell
.\run_streamlit.bat
```

### **3. Acessar no Navegador**

```
http://localhost:8501
```

---

## 📁 Estrutura do Projeto

```
PMO_Data/
├── streamlit_app.py                 ← 🆕 App principal
├── streamlit_pages/                 ← 🆕 Páginas
│   ├── __init__.py
│   ├── insert_results_page.py
│   ├── historic_page.py
│   └── dashboard_page.py
├── .streamlit/                      ← 🆕 Configuração
│   └── config.toml
├── backend.py                       ← ✅ Mantido 100%
├── utils/                           ← ✅ Mantido 100%
│   ├── models.py
│   ├── constants.py
│   └── styles.py
├── .cache/                          ← ✅ Cache persistente
│   └── pending_queue.json
├── requirements_streamlit.txt       ← 🆕 Dependências
└── README_STREAMLIT.md             ← 🆕 Este arquivo
```

---

## 🆚 Comparação: Rio vs Streamlit

| Recurso | Rio | Streamlit |
|---------|-----|-----------|
| **Facilidade de Deploy** | 🔸 Manual | ✅ Streamlit Cloud grátis |
| **Comunidade** | 🔸 Pequena | ✅ Grande |
| **Documentação** | 🔸 Limitada | ✅ Extensa |
| **Componentes** | 🔸 Básicos | ✅ Rico ecossistema |
| **Performance** | ✅ Reativo | 🔸 Rerun (mas otimizado) |
| **Curva aprendizado** | 🔸 Média | ✅ Simples |
| **Backend Integration** | ✅ Perfeito | ✅ Perfeito |

---

## ⚙️ Configurações

### Auto-Refresh
```python
# streamlit_app.py linha 128
AUTO_REFRESH_INTERVAL = 900  # 15 minutos
```

### Tema (cores)
```toml
# .streamlit/config.toml
[theme]
primaryColor = "#36454F"
backgroundColor = "#FFFAFA"
textColor = "#111827"
```

---

## 🎨 Visual

### Mantido 100%:
- ✅ Header preto
- ✅ Sidebar branca
- ✅ Cards de KPI com métricas
- ✅ Cores verde/vermelho para performance
- ✅ Layout responsivo
- ✅ Formulários de justificativa

### Melhorias:
- ✅ Mais responsivo em mobile
- ✅ Scroll mais suave
- ✅ Transições de página instantâneas
- ✅ Feedback visual melhorado

---

## 🚨 Troubleshooting

### Erro: "Module not found"
```bash
pip install -r requirements_streamlit.txt
```

### Logo não aparece
```python
# Verifique se wlogo.png está em PMO_Data/
ls wlogo.png
```

### Auto-refresh não funciona
```python
# O auto-refresh ocorre em background
# Verifique o console para ver logs:
# "⏰ [Auto-Refresh] Executando..."
```

### SharePoint travado
```
# Sistema detecta automaticamente:
# "🔒 [Backend] Arquivo travado por outro usuário"
# Dados ficam na fila e tentam novamente depois
```

---

## 🌐 Deploy em Produção

### **Opção 1: Streamlit Cloud (Recomendado)**

1. Commit código no GitHub:
```bash
git add .
git commit -m "Migração para Streamlit"
git push
```

2. Acesse: https://streamlit.io/cloud
3. Conecte seu GitHub
4. Deploy em 2 cliques! 🎉

### **Opção 2: Docker**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements_streamlit.txt .
RUN pip install -r requirements_streamlit.txt
COPY . .
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501"]
```

---

## 💡 Dicas

1. **Ctrl + R** - Rerun manual (atualiza dados)
2. **F11** - Fullscreen
3. **Sidebar** - Sempre acessível, mesmo em mobile
4. **Status** - Monitore pendências no menu

---

## 📞 Suporte

- Documentação Streamlit: https://docs.streamlit.io
- Sistema de Cache: Ver `SISTEMA_CACHE.md`
- Issues: Contate o desenvolvedor

---

**Desenvolvido com ❤️ usando Streamlit**

*Migrado do Rio em Dezembro 2025* ✨

