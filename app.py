from __future__ import annotations

from pathlib import Path

import streamlit as st

from questionario import render_questionario


APP_TITLE = "Sistema para Geração de Conceitos de Dispositivos Médicos"
APP_SUBTITLE = "Idealização → Conceito Aprovado"
SIDEBAR_TITLE = "Geração de Conceitos"
LOGO_PATH = Path("logo-msb.png")


def configurar_pagina() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🩺",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1250px;
        }

        .hero-card {
            padding: 2.4rem 2.8rem;
            border-radius: 18px;
            border: 1px solid rgba(120,120,120,0.25);
            background: linear-gradient(135deg, rgba(47,111,237,0.10), rgba(47,111,237,0.02));
        }

        .hero-card h1 {
            font-size: 2.55rem;
            margin-top: 0;
            margin-bottom: 1.4rem;
            color: #1f2937;
            line-height: 1.15;
        }

        .hero-card p {
            font-size: 1.08rem;
            line-height: 1.65;
            color: #111827;
            margin-bottom: 1rem;
        }

        div[data-testid="stSidebar"] {
            background-color: #f3f6fa;
        }

        div[data-testid="stSidebar"] h1 {
            font-size: 1.35rem;
            line-height: 1.3;
        }

        div.stButton > button {
            border-radius: 10px;
            min-height: 2.8rem;
            font-weight: 500;
        }

        div[data-testid="stSidebar"] img {
            border-radius: 8px;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inicializar_estado() -> None:
    if "page" not in st.session_state:
        st.session_state.page = "inicio"


def render_sidebar() -> None:
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        else:
            st.warning("Logo não encontrado: logo-msb.png")

        st.title(SIDEBAR_TITLE)
        st.caption(APP_SUBTITLE)

        st.write("")

        if st.button("🏠 Tela inicial", use_container_width=True):
            st.session_state.page = "inicio"
            st.rerun()

        if st.button("🧭 Abrir questionário", use_container_width=True):
            st.session_state.page = "questionario"
            st.rerun()


def render_inicio() -> None:
    st.markdown(
        """
<div class="hero-card">
<h1>Sistema para Geração de Conceitos de Dispositivos Médicos</h1>
<p>
Sistema adaptativo para apoiar a fase de idealização, análise inicial
e seleção de conceito em novos produtos médicos.
</p>
<p>
A ferramenta classifica o produto conforme sua estratégia de desenvolvimento,
origem da oportunidade, responsabilidade da empresa, contato com paciente,
esterilidade, fornecedor, nível de inovação, rota conceitual e principais
incertezas.
</p>
<p>
Ao final, o sistema recomenda um pacote enxuto de ferramentas para apoiar
a tomada de decisão, sem entrar na fase de projeto detalhado.
</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    if st.button("🚀 Iniciar questionário", type="primary", use_container_width=True):
        st.session_state.page = "questionario"
        st.rerun()


def main() -> None:
    configurar_pagina()
    inicializar_estado()
    render_sidebar()

    if st.session_state.page == "questionario":
        render_questionario()
    else:
        render_inicio()


if __name__ == "__main__":
    main()
