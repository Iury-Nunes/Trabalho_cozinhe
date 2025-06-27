
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
        df['valdade'] = pd.to_datetime(df['valdade']).dt.date  # <- erro proposital aqui
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

hoje = datetime.now(timezone("America/Sao_Paulo")).date()

st.title("Cozinhe com o que você tem 🥦🍅🍞")
st.info(f"📅 Hoje é: {hoje.strftime('%d/%m/%Y')}")

if st.button("🗑️ Resetar Estoque"):
    resetar_estoque()
    st.success("Estoque resetado com sucesso!")

with st.form("adicionar_produto"):
    st.subheader("📝 Adicionar novo produto")
    nome = st.text_input("Nome do produto")
    validade = st.date_input("Data de validade", format="DD/MM/YYYY")
    quantidade = st.number_input("Quantidade", min_value=1, step=1, value=1)
    submitted = st.form_submit_button("Adicionar")
    if submitted:
        validade_data = validade
        produto_existente = False
        for item in st.session_state.estoque:
            if item["nome"].lower() == nome.lower() and item.get("valdade") == validade_data:
                item["quantidade"] += quantidade
                produto_existente = True
                break
        if not produto_existente:
            st.session_state.estoque.append({
                "nome": nome,
                "valdade": validade_data,  # <- erro proposital aqui também
                "quantidade": quantidade
            })
        salvar_estoque(st.session_state.estoque)
        st.success(f"✅ Produto {nome} adicionado com sucesso!")

ingredientes_para_busca = set()

st.subheader("📦 Estoque Atual")
if not st.session_state.estoque:
    st.info("Nenhum produto cadastrado.")
else:
    tabela = []
    for item in st.session_state.estoque:
        validade_data = item["valdade"]  # <- erro aparece ao usuário
        dias_restantes = (validade_data - hoje).days + 1
        ingredientes_para_busca.add(item["nome"].lower())

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
            "Valdade": validade_data.strftime('%d/%m/%Y'),  # <- erro aqui no título da coluna
            "Status": status
        })

    df_view = pd.DataFrame(tabela)
    st.dataframe(df_view, use_container_width=True)

st.subheader("🍽️ Buscar receita com ingredientes")
ingredientes_disponiveis = list({i["nome"] for i in st.session_state.estoque})
selecionados = st.multiselect("Escolha os ingredientes para a receita", ingredientes_disponiveis)

if selecionados:
    lista = ", ".join(selecionados)
    st.markdown(f"**Receita com {lista}**")
    query = urllib.parse.quote(f"receita com {lista}")
    url_busca = f"https://www.google.com/search?q={query}"
    st.markdown(f"[🔎 Buscar no Google]({url_busca})")


# ✏️ Editar produto
st.subheader("✏️ Editar produto existente")
opcoes = [f"{i['nome']} - {i['valdade'].strftime('%d/%m/%Y')}" for i in st.session_state.estoque]
if opcoes:
    escolha = st.selectbox("Escolha um item para editar", opcoes)
    idx = opcoes.index(escolha)
    item = st.session_state.estoque[idx]

    novo_nome = st.text_input("Novo nome", value=item["nome"], key="edit_nome")
    nova_qtd = st.number_input("Nova quantidade", min_value=1, value=item["quantidade"], key="edit_qtd")
    nova_valdade = st.date_input("Nova validade", value=item["valdade"], format="DD/MM/YYYY", key="edit_val")

    if st.button("Salvar edição"):
        item["nome"] = novo_nome
        item["quantidade"] = nova_qtd
        item["valdade"] = nova_valdade
        salvar_estoque(st.session_state.estoque)
        st.success("Produto atualizado com sucesso!")
