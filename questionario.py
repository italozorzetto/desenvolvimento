
from __future__ import annotations

import json
from io import StringIO

import pandas as pd
import streamlit as st

from med_concept_engine import (
    MedConceptEngine,
    ToolPriority,
    ToolCategory,
    SelectedTool,
)


def init_engine() -> None:
    if "engine" not in st.session_state:
        st.session_state.engine = MedConceptEngine()
    if "last_error" not in st.session_state:
        st.session_state.last_error = ""


def reset_questionnaire() -> None:
    st.session_state.engine = MedConceptEngine()
    st.session_state.last_error = ""


def _priority_to_badge(priority: ToolPriority) -> str:
    if priority == ToolPriority.MANDATORY:
        return "✅ Obrigatória"
    if priority == ToolPriority.RECOMMENDED:
        return "🔵 Recomendada"
    return "⚪ Opcional"


def _tools_dataframe(selected: list[SelectedTool]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Prioridade": _priority_to_badge(item.priority),
            "Categoria": item.tool.category.value,
            "ID": item.tool.id,
            "Ferramenta": item.tool.name,
            "Justificativa": item.reason,
        }
        for item in selected
    ])


def render_questionario() -> None:
    """Renderiza o questionário adaptativo e os resultados.

    Esta função é chamada pelo app.py. Assim, a tela inicial fica separada
    e o questionário fica isolado como um módulo.
    """
    init_engine()
    engine: MedConceptEngine = st.session_state.engine

    st.title("Questionário Adaptativo")
    st.caption("Responda as perguntas. O sistema adapta o caminho e recomenda ferramentas para chegar ao conceito aprovado.")

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

    st.subheader(f"{current.id} — {current.text}")
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
            st.dataframe(pd.DataFrame(engine.profile.raw_answers), use_container_width=True)
        else:
            st.write("Nenhuma resposta registrada ainda.")


def render_resultados(engine: MedConceptEngine) -> None:
    selected = engine.apply_rules()
    profile = engine.profile
    grouped = engine.selected_as_groups(selected)

    st.success("Questionário concluído. As ferramentas foram recomendadas com base no perfil do produto.")

    st.header("Resumo do Perfil")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Complexidade", profile.complexity.name)
    c2.metric("Score", profile.complexity_score)
    c3.metric("Ferramentas", len(selected))
    c4.metric("Obrigatórias", len(grouped[ToolPriority.MANDATORY]))

    with st.expander("Perfil multicamadas completo", expanded=True):
        p = profile
        data = {
            "Estratégias": ", ".join(p.development_strategy) or "—",
            "Responsabilidades": ", ".join(p.company_responsibility) or "—",
            "Origem": p.project_origin or "—",
            "Usuário principal": p.user_type or "—",
            "Contato com paciente": "Sim" if p.has_patient_contact else "Não",
            "Invasividade": f"{p.invasiveness_level}/4",
            "Esterilidade necessária": "Sim" if p.sterility_required else "Não",
            "Esterilidade indefinida": "Sim" if p.sterility_unknown else "Não",
            "Componente digital": "Sim" if p.has_digital_component else "Não",
            "Medicamento/fluido associado": "Sim" if p.has_associated_drug else "Não",
            "Multi-stakeholder": "Sim" if p.multi_stakeholder else "Não",
            "Incerteza regulatória": p.regulatory_uncertainty or "—",
            "Incertezas de conceito": ", ".join(p.concept_uncertainties) or "nenhuma",
        }
        st.table(pd.DataFrame(data.items(), columns=["Campo", "Resultado"]))

    with st.expander("Score de complexidade", expanded=False):
        score_df = pd.DataFrame(
            [{"Fator": k, "Pontos": v} for k, v in profile.score_breakdown.items()]
        ).sort_values(by="Pontos", ascending=False)
        st.dataframe(score_df, use_container_width=True)

    st.header("Ferramentas Recomendadas")
    tabs = st.tabs(["✅ Obrigatórias", "🔵 Recomendadas", "⚪ Opcionais", "📋 Todas"])

    for tab, priority in zip(
        tabs[:3],
        [ToolPriority.MANDATORY, ToolPriority.RECOMMENDED, ToolPriority.OPTIONAL],
    ):
        with tab:
            render_tool_cards(grouped[priority])

    with tabs[3]:
        df = _tools_dataframe(selected)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.header("Relatório e Downloads")
    report = engine.generate_report(selected)
    json_data = engine.export_json_string(selected)
    csv_buffer = StringIO()
    _tools_dataframe(selected).to_csv(csv_buffer, index=False, sep=";")

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


def render_tool_cards(items: list[SelectedTool]) -> None:
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
