# ⚡ Quick Start - Streamlit Version

## 🚀 Começar em 3 Passos

### **1️⃣ Instalar**
```bash
pip install streamlit pandas openpyxl Office365-REST-Python-Client
```

### **2️⃣ Executar**
```bash
streamlit run streamlit_app.py
```

### **3️⃣ Abrir**
```
http://localhost:8501
```

**Pronto! 🎉**

---

## 📖 Funcionalidades Principais

### **Insert Results**
1. Selecione departamento no dropdown
2. Digite valor no campo "ACTUAL"
3. Se verde → clique "SEND"
4. Se vermelho → clique "JUSTIFY" e preencha

### **Historic**
1. Selecione departamento
2. Veja todos os meses (Jan-Dec)
3. Verde = meta atingida
4. Vermelho = abaixo da meta

### **Dashboard**
1. Selecione mês + departamento
2. Veja métricas: Total, On Target, Needs Action
3. Veja Top 3 / Bottom 3 KPIs

### **Refresh Data**
1. Clique no botão no menu lateral
2. Sistema baixa dados frescos do SharePoint
3. Processa fila de pendências

---

## 🎯 Comparação Rápida

### **Rio (Antes)**
```python
class PerformanceInputPage(rio.Component):
    active_page: str = "insert"
    menu_open: bool = False
    
    def build(self) -> rio.Component:
        return rio.Column(...)
```

**Problemas:**
- ❌ Classes complexas
- ❌ State management manual
- ❌ Pouca documentação

### **Streamlit (Agora)**
```python
if st.session_state.page == 'insert':
    insert_results_page.render()
```

**Vantagens:**
- ✅ Código simples
- ✅ State automático
- ✅ Muita documentação

---

## 🔧 Customização Rápida

### **Mudar Cores**
```toml
# .streamlit/config.toml
[theme]
primaryColor = "#FF0000"  ← Sua cor aqui
```

### **Mudar Tempo de Auto-Refresh**
```python
# streamlit_app.py linha 128
AUTO_REFRESH_INTERVAL = 1800  # 30 minutos
```

### **Adicionar Logo**
```python
# streamlit_app.py linha 167
st.image("seu_logo.png", width=60)
```

---

## ⚠️ Solução de Problemas

### **Erro: Command 'streamlit' not found**
```bash
pip install streamlit
```

### **Erro: Module 'backend' not found**
```bash
# Certifique-se de estar na pasta PMO_Data
cd PMO_Data
streamlit run streamlit_app.py
```

### **Erro: Port 8501 already in use**
```bash
streamlit run streamlit_app.py --server.port 8502
```

### **Visual quebrado**
```bash
# Limpar cache
streamlit cache clear
# Restart
streamlit run streamlit_app.py
```

---

## 📱 Atalhos Úteis

| Atalho | Ação |
|--------|------|
| **R** | Rerun app |
| **C** | Limpar cache |
| **Ctrl + Click** | Ver source |
| **F11** | Fullscreen |

---

## 🎓 Aprenda Mais

### **5 Minutos:**
- [Streamlit Basics](https://docs.streamlit.io/get-started/fundamentals/main-concepts)

### **15 Minutos:**
- [Session State Tutorial](https://docs.streamlit.io/develop/tutorials/databases/session-state)

### **30 Minutos:**
- [Build a Full App](https://docs.streamlit.io/develop/tutorials/databases)

---

## 🌟 Features Especiais

### **Auto-Refresh Inteligente**
- ⏰ A cada 15 minutos automaticamente
- 🔄 Manual via botão "Refresh Data"
- 💾 Processa fila de pendências
- ✅ SharePoint sempre prevalece

### **Sistema de Cache**
- 📝 Salva tudo localmente primeiro
- ☁️ Tenta subir para SharePoint
- 🔒 Se travado, mantém na fila
- 🔄 Retry automático depois

### **Merge Inteligente**
- 👑 SharePoint = Verdade
- 💾 Cache = Backup
- 🤝 Merge sem conflitos
- ✅ Dados nunca perdidos

---

## 🚀 Deploy em Produção

### **Streamlit Cloud (Grátis)**
1. Push para GitHub
2. https://streamlit.io/cloud
3. Connect repository
4. Deploy! ✨

**URL pública em 2 minutos!**

---

## 💡 Dicas Pro

1. **Use Ctrl+R** para recarregar rápido
2. **Monitore pendências** no menu
3. **Refresh manual** se dados parecem antigos
4. **Verifique logs** no terminal
5. **Sidebar sempre visível** em telas grandes

---

## ✅ Checklist de Teste

- [ ] App abre sem erros
- [ ] Logo aparece
- [ ] Menu funciona
- [ ] Pode trocar páginas
- [ ] Pode selecionar dept
- [ ] Pode adicionar KPI
- [ ] Pode ver histórico
- [ ] Pode ver dashboard
- [ ] Refresh funciona
- [ ] Pendências aparecem

**Tudo OK? Você está pronto! 🎉**

---

## 📞 Ajuda

**Problemas?**
1. Leia `README_STREAMLIT.md`
2. Veja `MIGRATION_GUIDE.md`
3. Consulte `SISTEMA_CACHE.md`
4. Check Streamlit docs

**Suporte direto:** Contate desenvolvedor

---

**Happy Coding! 🚀✨**

