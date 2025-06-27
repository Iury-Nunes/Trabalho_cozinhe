
import streamlit as st
from datetime import datetime

# Inicializa o estoque na sessão
if 'estoque' not in st.session_state:
    st.session_state.estoque = []

st.title("Cozinhe com o que você tem 🥦🍅🍞")
st.markdown("Organize seu estoque de alimentos e evite desperdícios.")

# Formulário para adicionar produto
with st.form("adicionar_produto"):
    st.subheader("Adicionar novo produto")
    nome = st.text_input("Nome do produto")
    validade = st.date_input("Data de validade", format="DD/MM/YYYY")
    submitted = st.form_submit_button("Adicionar")
    if submitted:
        st.session_state.estoque.append({
            "nome": nome,
            "validade": datetime.combine(validade, datetime.min.time())
        })
        st.success(f"Produto '{nome}' adicionado com sucesso!")

# Mostrar estoque atual
st.subheader("Estoque Atual")
if not st.session_state.estoque:
    st.info("Nenhum produto cadastrado.")
else:
    hoje = datetime.today().date()
    for item in st.session_state.estoque:
        dias_restantes = (item["validade"].date() - hoje).days
        status = "✅ OK"
        if dias_restantes < 0:
            status = "❌ VENCIDO"
        elif dias_restantes == 0:
            status = "⚠️ Vence HOJE"
        elif dias_restantes <= 3:
            status = "⚠️ Vence em até 3 dias"
        elif dias_restantes <= 7:
            status = "🕒 Vence em até 1 semana"
        elif dias_restantes <= 30:
            status = "📅 Vence em até 1 mês"

        st.write(f"**{item['nome']}** - Validade: {item['validade'].strftime('%d/%m/%Y')} - {status}")
