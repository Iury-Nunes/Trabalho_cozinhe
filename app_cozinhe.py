
import streamlit as st
from datetime import datetime
import pandas as pd
from pathlib import Path
from pytz import timezone
import requests

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

def buscar_receitas(ingrediente):
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={ingrediente}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("meals", [])
    except Exception:
        return []
    return []

if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_estoque()

hoje = datetime.now(timezone("America/Sao_Paulo")).date()

st.markdown("<h1 style='color:#6C3483;'>Cozinhe com o que você tem 🥦🍅🍞</h1>", unsafe_allow_html=True)
st.info(f"📅 Hoje é: {hoje.strftime('%d/%m/%Y')}")

# Botão para resetar
if st.button("🗑️ Resetar Estoque"):
    resetar_estoque()
    st.success("Estoque resetado com sucesso!")

# Formulário para adicionar item
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

# Editar item existente
st.markdown("### ✏️ Editar produto existente")
nomes_produtos = [f"{i['nome']} - {i['validade'].strftime('%d/%m/%Y')}" for i in st.session_state.estoque]
if nomes_produtos:
    item_escolhido = st.selectbox("Selecione um item para editar", nomes_produtos)
    indice = nomes_produtos.index(item_escolhido)
    item = st.session_state.estoque[indice]
    novo_nome = st.text_input("Novo nome", value=item["nome"], key="edit_nome")
    nova_quantidade = st.number_input("Nova quantidade", value=item["quantidade"], min_value=1, key="edit_qtd")
    nova_validade = st.date_input("Nova validade", value=item["validade"], format="DD/MM/YYYY", key="edit_val")
    if st.button("Salvar edição"):
        item["nome"] = novo_nome
        item["quantidade"] = nova_quantidade
        item["validade"] = nova_validade
        salvar_estoque(st.session_state.estoque)
        st.success("Produto atualizado com sucesso!")

# Exibir estoque
st.markdown("### 📦 Estoque Atual")
if not st.session_state.estoque:
    st.info("Nenhum produto cadastrado.")
else:
    tabela = []
    ingredientes_para_busca = set()
    for item in st.session_state.estoque:
        validade_data = item["validade"]
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

# Exibir receitas
st.markdown("### 🍽️ Receitas com seu estoque")
for ingrediente in ingredientes_para_busca:
    st.markdown(f"#### 🔍 Receitas com **{ingrediente}**:")
    receitas = buscar_receitas(ingrediente)
    if not receitas:
        st.warning("Nenhuma receita encontrada.")
    else:
        for receita in receitas[:3]:
            st.markdown(f"- [{receita['strMeal']}]({receita['strSource'] or 'https://www.themealdb.com/meal/' + receita['idMeal']})")
            st.image(receita['strMealThumb'], width=200)
