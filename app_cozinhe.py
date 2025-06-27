
import streamlit as st
from datetime import datetime
import pandas as pd
from pathlib import Path

ARQUIVO_EXCEL = "estoque_produtos.xlsx"

# Carregar dados se o arquivo já existir
def carregar_estoque():
    if Path(ARQUIVO_EXCEL).exists():
        df = pd.read_excel(ARQUIVO_EXCEL)
        df['validade'] = pd.to_datetime(df['validade'])
        return df.to_dict(orient="records")
    return []

# Salvar estoque no Excel
def salvar_estoque(estoque):
    df = pd.DataFrame(estoque)
    df.to_excel(ARQUIVO_EXCEL, index=False)

# Resetar estoque
def resetar_estoque():
    st.session_state.estoque = []
    if Path(ARQUIVO_EXCEL).exists():
        Path(ARQUIVO_EXCEL).unlink()

# Inicializa o estoque
if 'estoque' not in st.session_state:
    st.session_state.estoque = carregar_estoque()

# Estilo do app
st.markdown("<h1 style='color:#6C3483;'>Cozinhe com o que você tem 🥦🍅🍞</h1>", unsafe_allow_html=True)
st.markdown("Organize seu estoque de alimentos e **evite desperdícios** com praticidade.")

# Botão para resetar o estoque
if st.button("🗑️ Resetar Estoque"):
    if st.confirm("Tem certeza que deseja apagar todos os dados do estoque?"):
        resetar_estoque()
        st.success("Estoque resetado com sucesso!")

# Formulário para adicionar produto
with st.form("adicionar_produto"):
    st.markdown("### 📝 Adicionar novo produto")
    nome = st.text_input("Nome do produto")
    validade = st.date_input("Data de validade", format="DD/MM/YYYY")
    quantidade = st.number_input("Quantidade", min_value=1, step=1, value=1)
    submitted = st.form_submit_button("Adicionar")
    if submitted:
        novo_item = {
            "nome": nome,
            "validade": validade,
            "quantidade": quantidade
        }
        st.session_state.estoque.append(novo_item)
        salvar_estoque(st.session_state.estoque)
        st.success(f"✅ Produto **{nome}** adicionado com sucesso!")

# Mostrar estoque
st.markdown("### 📦 Estoque Atual")
if not st.session_state.estoque:
    st.info("Nenhum produto cadastrado.")
else:
    hoje = datetime.today().date()
    tabela = []
    for item in st.session_state.estoque:
        validade_data = item["validade"].date() if isinstance(item["validade"], datetime) else item["validade"]
        dias_restantes = (validade_data - hoje).days

        if dias_restantes < 0:
            status = "❌ VENCIDO"
        elif dias_restantes == 0:
            status = "⚠️ Vence HOJE"
        elif dias_restantes == 1:
            status = "⚠️ Vence AMANHÃ"
        elif 2 <= dias_restantes <= 7:
            status = f"⚠️ Vence em {dias_restantes} dias"
        elif 8 <= dias_restantes <= 30:
            semanas = dias_restantes // 7
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
