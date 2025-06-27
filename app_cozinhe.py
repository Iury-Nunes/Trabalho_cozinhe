
import streamlit as st
from datetime import datetime
import pandas as pd
from pathlib import Path
from pytz import timezone
import urllib.parse

ARQUIVO_EXCEL = "estoque_produtos.xlsx"

def carregar_estoque():
    if Path(ARQUIVO_EXCEL).exists():
        df = pd.read_excel(ARQUIVO_EXCEL)
        df['validade'] = pd.to_datetime(df['validade']).dt.date
        return df.to_dict(orient="records")
    return []

def salvar_estoque(estoque):
    df = pd.DataFrame(estoque)
    df.to_excel(ARQUIVO_EXCEL, index=False)

def resetar_estoque():
    st.session_state.estoque = []
    if Path(ARQUIVO_EXCEL).exists():
        Path(ARQUIVO_EXCEL).unlink()

if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_estoque()

# Aplicar fuso horário de São Paulo
hoje = datetime.now(timezone("America/Sao_Paulo")).date()

st.markdown("<h1 style='color:#6C3483;'>Cozinhe com o que você tem 🥦🍅🍞</h1>", unsafe_allow_html=True)
st.markdown("Organize seu estoque de alimentos e **evite desperdícios** com praticidade.")
st.info(f"📅 Hoje é: {hoje.strftime('%d/%m/%Y')}")

if st.button("🗑️ Resetar Estoque"):
    resetar_estoque()
    st.success("Estoque resetado com sucesso!")

with st.form("adicionar_produto"):
    st.markdown("### 📝 Adicionar novo produto")
    nome = st.text_input("Nome do produto")
    validade = st.date_input("Data de validade", format="DD/MM/YYYY")
    quantidade = st.number_input("Quantidade", min_value=1, step=1, value=1)
    submitted = st.form_submit_button("Adicionar")
    if submitted:
        validade_data = validade
        produto_existente = False
        for item in st.session_state.estoque:
            if item["nome"].lower() == nome.lower() and item["validade"] == validade_data:
                item["quantidade"] += quantidade
                produto_existente = True
                break
        if not produto_existente:
            st.session_state.estoque.append({
                "nome": nome,
                "validade": validade_data,
                "quantidade": quantidade
            })
        salvar_estoque(st.session_state.estoque)
        st.success(f"✅ Produto **{nome}** adicionado com sucesso!")

# Se houver estoque, mostrar tabela e opções de edição
st.markdown("### 📦 Estoque Atual")
if not st.session_state.estoque:
    st.info("Nenhum produto cadastrado.")
else:
    tabela = []
    for item in st.session_state.estoque:
        validade_data = item["validade"]
        dias_restantes = (validade_data - hoje).days + 1

        if dias_restantes <= 0:
            status = "❌ VENCIDO"
        elif dias_restantes == 1:
            status = "⚠️ Vence HOJE"
        elif dias_restantes == 2:
            status = "⚠️ Vence AMANHÃ"
        elif 3 <= dias_restantes <= 8:
            status = f"⚠️ Vence em {dias_restantes - 1} dias"
        elif 9 <= dias_restantes <= 31:
            semanas = (dias_restantes - 1) // 7
            status = f"📅 Vence em {semanas} semana(s)"
        else:
            status = "🟢 Válido por mais de 1 mês"

        tabela.append({
            "Produto": item["nome"],
            "Quantidade": item["quantidade"],
            "Validade": validade_data.strftime('%d/%m/%Y'),
            "Status": status
        })

    df_view = pd.DataFrame(tabela)
    st.dataframe(df_view.style.applymap(
        lambda val: "color: red;" if "VENCIDO" in val else (
            "color: orange;" if "HOJE" in val or "AMANHÃ" in val or "dias" in val else (
                "color: #9C27B0;" if "semana" in val else (
                    "color: #2874A6;" if "mês" in val else "color: green;"
                )
            )
        ), subset=["Status"]
    ), use_container_width=True)

    # ✏️ Edição de produto
    st.markdown("### ✏️ Editar produto")
    opcoes = [f"{i['nome']} - {i['validade'].strftime('%d/%m/%Y')}" for i in st.session_state.estoque]
    escolha = st.selectbox("Escolha um item para editar", opcoes)
    idx = opcoes.index(escolha)
    item = st.session_state.estoque[idx]

    novo_nome = st.text_input("Novo nome", value=item["nome"])
    nova_qtd = st.number_input("Nova quantidade", min_value=1, value=item["quantidade"])
    nova_validade = st.date_input("Nova validade", value=item["validade"], format="DD/MM/YYYY")

    if st.button("Salvar edição"):
        item["nome"] = novo_nome
        item["quantidade"] = nova_qtd
        item["validade"] = nova_validade
        salvar_estoque(st.session_state.estoque)
        st.success("Produto atualizado com sucesso!")

    # 🔎 Sugestão de busca de receita
    st.markdown("### 🍽️ Buscar receita com ingredientes")
    ingredientes_disponiveis = list({i["nome"] for i in st.session_state.estoque})
    selecionados = st.multiselect("Escolha os ingredientes para a receita", ingredientes_disponiveis)

    if selecionados:
        lista = ", ".join(selecionados)
        st.markdown(f"**Receita com {lista}**")
        query = urllib.parse.quote(f"receita com {lista}")
        url_busca = f"https://www.google.com/search?q={query}"
        st.markdown(f"[🔎 Buscar no Google]({url_busca})")
