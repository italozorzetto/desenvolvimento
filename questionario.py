from __future__ import annotations

from io import StringIO

import pandas as pd
import streamlit as st

from med_concept_engine import (
    MedConceptEngine,
    ToolPriority,
    ToolCategory,
    SelectedTool,
)


# =============================================================================
# ESTADO / INICIALIZAÇÃO
# =============================================================================

def init_engine() -> None:
    if "engine" not in st.session_state:
        st.session_state.engine = MedConceptEngine()

    if "last_error" not in st.session_state:
        st.session_state.last_error = ""


def reset_questionnaire() -> None:
    st.session_state.engine = MedConceptEngine()
    st.session_state.last_error = ""


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def _priority_to_badge(priority: ToolPriority) -> str:
    if priority == ToolPriority.MANDATORY:
        return "✅ Obrigatória"

    if priority == ToolPriority.RECOMMENDED:
        return "🔵 Recomendada"

    return "⚪ Opcional"


def _is_go_no_go_tool(item: SelectedTool) -> bool:
    """
    Identifica ferramentas Go/No-Go para não exibir no pacote principal.

    A matriz Go/No-Go deve acontecer dentro de cada Gate, mas não deve entrar
    como ferramenta comum na lista de ferramentas recomendadas ao usuário.
    """
    name = item.tool.name.lower()
    tool_id = item.tool.id.lower()

    terms = [
        "go/no-go",
        "go / no-go",
        "go no-go",
        "go/no go",
        "matriz go",
        "no-go",
        "no go",
    ]

    return any(term in name for term in terms) or "gonogo" in tool_id


def _visible_package_tools(items: list[SelectedTool]) -> list[SelectedTool]:
    """Remove ferramentas Go/No-Go da lista visual de pacote."""
    return [item for item in items if not _is_go_no_go_tool(item)]


def _compact_tools_dataframe(selected: list[SelectedTool]) -> pd.DataFrame:
    """
    Tabela simples para exibição e download:
    somente Gate e Ferramenta.
    """
    return pd.DataFrame([
        {
            "Gate": st.session_state.engine.tool_gate_label(item.tool.id)
            if "engine" in st.session_state else "—",
            "Ferramenta": item.tool.name,
        }
        for item in selected
    ])


def _hidden_tools_dataframe(engine: MedConceptEngine, hidden: list[SelectedTool]) -> pd.DataFrame:
    """
    Tabela interna para desenvolvedor.
    Aqui ainda mostramos categoria e prioridade para análise das regras.
    """
    return pd.DataFrame([
        {
            "Gate": engine.tool_gate_label(item.tool.id),
            "Ferramenta": item.tool.name,
            "Categoria": item.tool.category.value,
            "Prioridade": _priority_to_badge(item.priority),
        }
        for item in hidden
    ])


def _tools_dataframe_detailed(selected: list[SelectedTool]) -> pd.DataFrame:
    """
    Tabela detalhada mantida para uso interno futuro.
    Não é usada na tela principal, mas pode ser útil em melhorias.
    """
    return pd.DataFrame([
        {
            "Prioridade": _priority_to_badge(item.priority),
            "Gate": st.session_state.engine.tool_gate_label(item.tool.id)
            if "engine" in st.session_state else "—",
            "Categoria": item.tool.category.value,
            "ID": item.tool.id,
            "Ferramenta": item.tool.name,
            "Justificativa": item.reason,
        }
        for item in selected
    ])


# =============================================================================
# QUESTIONÁRIO
# =============================================================================

def render_questionario() -> None:
    """
    Renderiza o questionário adaptativo e os resultados.

    Esta função é chamada pelo app.py. Assim, a tela inicial fica separada
    e o questionário fica isolado como um módulo.
    """
    init_engine()
    engine: MedConceptEngine = st.session_state.engine

    col_a, col_b, col_c = st.columns([1, 1, 2])

    with col_a:
        if st.button("🔄 Reiniciar questionário", use_container_width=True):
            reset_questionnaire()
            st.rerun()

    with col_b:
        if st.button("🏠 Voltar ao início", use_container_width=True):
            st.session_state.page = "inicio"
            st.rerun()

    answered, total, progress = engine.progress()

    st.progress(progress)
    st.caption(f"Perguntas respondidas: {answered} de aproximadamente {total}")

    if st.session_state.last_error:
        st.error(st.session_state.last_error)

    current = engine.get_current_question()

    if current is None:
        render_resultados(engine)
        return

    # Mostra somente a pergunta, sem Q01, Q02 etc.
    st.subheader(current.text)

    if current.help_text:
        st.info(current.help_text)

    with st.form(key=f"form_{current.id}", clear_on_submit=False):
        if current.multiple:
            selected_labels = st.multiselect(
                "Selecione uma ou mais opções:",
                options=list(current.options.keys()),
                format_func=lambda key: f"{key}) {current.options[key]}",
                key=f"answer_{current.id}",
            )
            answer_value = selected_labels
        else:
            answer_value = st.radio(
                "Selecione uma opção:",
                options=list(current.options.keys()),
                format_func=lambda key: f"{key}) {current.options[key]}",
                key=f"answer_{current.id}",
            )

        submitted = st.form_submit_button("Avançar", use_container_width=True)

    if submitted:
        try:
            engine.answer_current_question(answer_value)
            st.session_state.last_error = ""
            st.rerun()
        except Exception as exc:
            st.session_state.last_error = str(exc)
            st.rerun()

    with st.expander("Ver respostas já registradas"):
        if engine.profile.raw_answers:
            st.dataframe(
                pd.DataFrame(engine.profile.raw_answers),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write("Nenhuma resposta registrada ainda.")


# =============================================================================
# RESULTADOS
# =============================================================================

def render_resultados(engine: MedConceptEngine) -> None:
    """
    Renderiza a tela final de resultados.

    Ajustes desta versão:
    - Remove resumo do perfil.
    - Remove perfil multicamadas da tela.
    - Mantém apenas score de complexidade.
    - Mostra Pacote de Ferramentas por Gate.
    - Remove justificativas da tabela principal.
    - Remove Go/No-Go da lista visual de ferramentas.
    - Candidatas ocultas só aparecem se usuário confirmar que é desenvolvedor.
    - Mantém Relatório e Downloads.
    """
    selected_all = engine.apply_rules()
    raw_candidates_all = engine.apply_rules_raw()
    profile = engine.profile

    # Remove Go/No-Go da lista visual e dos downloads de ferramentas.
    selected = _visible_package_tools(selected_all)
    raw_candidates = _visible_package_tools(raw_candidates_all)

    st.success("Questionário concluído.")

    with st.expander("Score de complexidade", expanded=True):
        st.markdown(
            f"""
            **Complexidade identificada:** {profile.complexity.name}  
            **Score:** {profile.complexity_score}
            """
        )

        score_df = pd.DataFrame(
            [{"Fator": k, "Pontos": v} for k, v in profile.score_breakdown.items()]
        ).sort_values(by="Pontos", ascending=False)

        st.dataframe(
            score_df,
            use_container_width=True,
            hide_index=True,
            height=min(360, 42 + 36 * len(score_df)),
        )

    st.header("Pacote de Ferramentas")

    tabs = st.tabs(["🧭 Gates", "🔎 Candidatas ocultas"])

    with tabs[0]:
        render_tool_cards_by_gate(engine, selected)

    with tabs[1]:
        st.markdown("### Área de revisão interna")

        resposta_dev = st.radio(
            "Você é o desenvolvedor?",
            options=["Não", "Sim"],
            horizontal=True,
            key="developer_access_hidden_tools",
        )

        if resposta_dev == "Sim":
            hidden = [
                item for item in raw_candidates
                if item.tool.id not in {s.tool.id for s in selected}
            ]

            if hidden:
                st.caption(
                    "Ferramentas acionadas pelas regras, mas removidas da saída principal "
                    "para manter o pacote enxuto."
                )

                st.dataframe(
                    _hidden_tools_dataframe(engine, hidden),
                    use_container_width=True,
                    hide_index=True,
                    height=min(520, 42 + 35 * len(hidden)),
                )
            else:
                st.info("Nenhuma ferramenta oculta.")
        else:
            st.info("As ferramentas candidatas ocultas são exibidas apenas para revisão interna.")

    st.header("Relatório e Downloads")

    # Relatório e JSON seguem o pacote visível, sem Go/No-Go como ferramenta comum.
    # As matrizes Go/No-Go devem entrar futuramente como seção própria do relatório.
    report = engine.generate_report(selected)
    json_data = engine.export_json_string(selected)

    csv_buffer = StringIO()
    _compact_tools_dataframe(selected).to_csv(csv_buffer, index=False, sep=";")

    with st.expander("Prévia do Concept Report", expanded=False):
        st.text_area("Relatório", report, height=500)

    d1, d2, d3 = st.columns(3)

    with d1:
        st.download_button(
            label="📄 Baixar relatório TXT",
            data=report.encode("utf-8"),
            file_name="concept_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with d2:
        st.download_button(
            label="📦 Baixar JSON",
            data=json_data.encode("utf-8"),
            file_name="concept_report.json",
            mime="application/json",
            use_container_width=True,
        )

    with d3:
        st.download_button(
            label="📊 Baixar ferramentas CSV",
            data=csv_buffer.getvalue().encode("utf-8"),
            file_name="ferramentas_recomendadas.csv",
            mime="text/csv",
            use_container_width=True,
        )


# =============================================================================
# EXIBIÇÃO DAS FERRAMENTAS
# =============================================================================

def render_tool_cards_by_gate(engine: MedConceptEngine, items: list[SelectedTool]) -> None:
    """
    Exibe as ferramentas agrupadas por Gate, com layout limpo.

    Mostra somente:
    - Gate
    - Nome da ferramenta

    Não mostra:
    - prioridade;
    - categoria;
    - ID;
    - justificativa.
    """
    if not items:
        st.info("Nenhuma ferramenta selecionada.")
        return

    by_gate: dict[int, list[SelectedTool]] = {}

    for item in items:
        by_gate.setdefault(engine.tool_gate(item.tool.id), []).append(item)

    for gate in sorted(by_gate):
        gate_label = engine.tool_gate_label(by_gate[gate][0].tool.id)

        st.markdown(f"### {gate_label}")

        df_gate = pd.DataFrame([
            {"Ferramenta": item.tool.name}
            for item in by_gate[gate]
        ])

        st.dataframe(
            df_gate,
            use_container_width=True,
            hide_index=True,
            height=min(260, 42 + 36 * len(df_gate)),
        )


def render_tool_cards(items: list[SelectedTool]) -> None:
    """
    Função antiga mantida para compatibilidade.
    Não é usada na tela principal atual.
    """
    if not items:
        st.info("Nenhuma ferramenta neste grupo.")
        return

    by_category: dict[ToolCategory, list[SelectedTool]] = {}

    for item in items:
        by_category.setdefault(item.tool.category, []).append(item)

    for category, tools in by_category.items():
        st.subheader(category.value)

        for item in tools:
            with st.container(border=True):
                st.markdown(f"**[{item.tool.id}] {item.tool.name}**")
                st.write(item.tool.description)
                st.caption(f"Justificativa: {item.reason}")
