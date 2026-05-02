
from __future__ import annotations

import streamlit as st

from questionario import render_questionario


APP_TITLE = "Med Concept Engine"


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
        }
        .hero-card {
            padding: 2rem;
            border-radius: 18px;
            border: 1px solid rgba(120,120,120,0.25);
            background: linear-gradient(135deg, rgba(47,111,237,0.10), rgba(47,111,237,0.02));
        }
        .small-card {
            padding: 1.2rem;
            border-radius: 14px;
            border: 1px solid rgba(120,120,120,0.22);
            height: 100%;
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
        st.title("🩺 Med Concept")
        st.caption("Idealização → Conceito Aprovado")

        if st.button("🏠 Tela inicial", use_container_width=True):
            st.session_state.page = "inicio"
            st.rerun()

        if st.button("🧭 Abrir questionário", use_container_width=True):
            st.session_state.page = "questionario"
            st.rerun()

        st.divider()
        st.markdown("**Estrutura do app**")
        st.markdown(
            """
            - `app.py`: tela inicial e navegação  
            - `questionario.py`: questionário adaptativo  
            - `med_concept_engine.py`: regras, perguntas e relatório  
            """
        )


def render_inicio() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <h1>Med Concept Engine</h1>
            <p style="font-size: 1.15rem;">
                Sistema adaptativo para apoiar a fase de idealização e seleção de conceito
                em novos produtos médicos.
            </p>
            <p>
                A ferramenta classifica o produto por estratégia de desenvolvimento, responsabilidade
                da empresa, contato com paciente, esterilidade, fornecedor, inovação, regulatório,
                fabricação e incertezas. Ao final, recomenda as ferramentas adequadas para chegar
                ao conceito aprovado e preparar a entrega ao time de projeto.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="small-card">
                <h3>1. Triagem do produto</h3>
                <p>Identifica se é OEM, white label, adaptação, novo kit, acessório,
                inovação, internalização ou substituição de fornecedor.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="small-card">
                <h3>2. Motor de regras</h3>
                <p>As respostas acionam ferramentas específicas com prioridade e justificativa,
                em vez de usar apenas uma classificação simples.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="small-card">
                <h3>3. Entrega ao projeto</h3>
                <p>Gera ferramentas recomendadas, relatório TXT, JSON estruturado e CSV
                para uso na próxima etapa.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    st.subheader("Fluxo da ferramenta")
    st.markdown(
        """
        **Tela inicial** → **Questionário adaptativo** → **Perfil multicamadas** →
        **Ferramentas recomendadas** → **Concept Report** → **Pacote de transferência ao projeto**
        """
    )

    st.info(
        "O escopo termina no conceito aprovado. A fase posterior de projeto detalhado, "
        "FMEA completo, gerenciamento formal de risco, cálculos, verificação e validação "
        "deve ficar com o time de projeto."
    )

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
