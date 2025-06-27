
import streamlit as st
from datetime import datetime
import pandas as pd
from pathlib import Path
from pytz import timezone
import requests
from pyfood.utils import Shelf

ARQUIVO_EXCEL = "estoque_produtos.xlsx"

# Inicializa o tradutor Pyfood
shelf = Shelf(region='Canada', month_id=0, source='PT')

def traduzir_ingrediente(ingrediente):
    try:
        res = shelf.process_ingredients([ingrediente], lang_dest='EN')
        return res['ingredients_by_taxon'][0][0].lower()
    except Exception:
        return ingrediente.lower()

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
    ingrediente_en = traduzir_ingrediente(ingrediente)
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={ingrediente_en}"
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

ingredientes_para_busca = set()

st.subheader("📦 Estoque Atual")
if not st.session_state.estoque:
    st.info("Nenhum produto cadastrado.")
else:
    tabela = []
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
    st.dataframe(df_view, use_container_width=True)

st.subheader("🍽️ Receitas com seu estoque")
receitas_unicas = {}
for ingrediente in ingredientes_para_busca:
    lista = buscar_receitas(ingrediente)
    for r in lista or []:
        receitas_unicas[r['idMeal']] = r

if not receitas_unicas:
    st.warning("Nenhuma receita encontrada com os ingredientes cadastrados.")
else:
    for receita in list(receitas_unicas.values())[:6]:
        st.markdown(f"**{receita['strMeal']}**")
        st.image(receita['strMealThumb'], width=200)
        st.markdown(f"[🔗 Ver receita](https://www.themealdb.com/meal/{receita['idMeal']})")
