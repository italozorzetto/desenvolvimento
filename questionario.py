from __future__ import annotations

from io import StringIO

import pandas as pd
import streamlit as st

from med_concept_engine import (
    MedConceptEngine,
    SelectedTool,
    ToolCategory,
    ToolPriority,
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
    return priority.value


def _tools_dataframe(engine: MedConceptEngine, selected: list[SelectedTool]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Gate": engine.tool_gate_label(item.tool.id),
            "Prioridade": _priority_to_badge(item.priority),
            "Categoria": item.tool.category.value,
            "ID": item.tool.id,
            "Ferramenta": item.tool.name,
            "Justificativa": item.reason,
            "Subferramentas": ", ".join(item.tool.subtools) if item.tool.subtools else "—",
        }
        for item in selected
    ])


def render_questionario() -> None:
    """Renderiza o questionário adaptativo e os resultados."""
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
            st.session_state.last_error = ""
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

    st.subheader(current.text)
    if current.help_text:
        st.info(current.help_text)

    with st.form(key=f"form_{current.id}", clear_on_submit=False):
        if current.multiple:
            answer_value = st.multiselect(
                "Selecione uma ou mais opções:",
                options=list(current.options.keys()),
                format_func=lambda key: f"{key}) {current.options[key]}",
                key=f"answer_{current.id}",
            )
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

    with st.expander("Ver respostas já registradas", expanded=False):
        if engine.profile.raw_answers:
            st.dataframe(pd.DataFrame(engine.profile.raw_answers), use_container_width=True, hide_index=True)
        else:
            st.write("Nenhuma resposta registrada ainda.")


def render_resultados(engine: MedConceptEngine) -> None:
    selected = engine.apply_rules()
    raw_candidates = engine.apply_rules_raw()
    profile = engine.profile
    grouped = engine.selected_as_groups(selected)

    st.success("Questionário concluído. O sistema gerou um pacote inteligente para este perfil de produto.")

    st.header("Resumo do Perfil")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Rota", engine.project_route())
    c2.metric("Complexidade", profile.complexity.name)
    c3.metric("Score", profile.complexity_score)
    c4.metric("Pacote", len(selected))
    c5.metric("Candidatas", len(raw_candidates))

    st.info(
        f"O algoritmo encontrou {len(raw_candidates)} ferramentas candidatas, "
        f"mas exibiu {len(selected)} no pacote principal, respeitando o limite de "
        f"até {engine.recommendation_cap()} ferramentas para esta rota."
    )

    with st.expander("Perfil multicamadas completo", expanded=False):
        p = profile
        data = {
            "Estratégias": ", ".join(p.development_strategy) or "—",
            "Responsabilidades": ", ".join(p.company_responsibility) or "—",
            "Origem": p.project_origin or "—",
            "Classe regulatória": p.regulatory_class.name,
            "Usuário principal": p.user_type or "—",
            "Contato com paciente": "Sim" if p.has_patient_contact else "Não",
            "Invasividade": f"{p.invasiveness_level}/4",
            "Esterilidade necessária": "Sim" if p.sterility_required else "Não",
            "Esterilidade indefinida": "Sim" if p.sterility_unknown else "Não",
            "Componente digital": "Sim" if p.has_digital_component else "Não",
            "Medicamento/fluido associado": "Sim" if p.has_associated_drug else "Não",
            "Uso crítico": "Sim" if p.critical_use else "Não",
            "Multi-stakeholder": "Sim" if p.multi_stakeholder else "Não",
            "Incerteza regulatória": p.regulatory_uncertainty or "—",
            "Incertezas de conceito": ", ".join(p.concept_uncertainties) or "nenhuma",
        }
        st.table(pd.DataFrame(data.items(), columns=["Campo", "Resultado"]))

    with st.expander("Score de complexidade", expanded=False):
        score_df = pd.DataFrame(
            [{"Fator": k, "Pontos": v} for k, v in profile.score_breakdown.items()]
        ).sort_values(by="Pontos", ascending=False)
        st.dataframe(score_df, use_container_width=True, hide_index=True)

    st.header("Pacote Inteligente de Ferramentas")
    tabs = st.tabs([
        "🧭 Por Gate",
        "✅ Obrigatórias",
        "🔵 Recomendadas",
        "⚪ Opcionais",
        "📋 Pacote",
        "🧪 Candidatas ocultas",
        "🧾 Go/No-Go",
    ])

    with tabs[0]:
        render_tool_cards_by_gate(engine, selected)

    for tab, priority in zip(
        tabs[1:4],
        [ToolPriority.MANDATORY, ToolPriority.RECOMMENDED, ToolPriority.OPTIONAL],
    ):
        with tab:
            render_tool_cards(grouped[priority])

    with tabs[4]:
        df = _tools_dataframe(engine, selected)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[5]:
        selected_ids = {item.tool.id for item in selected}
        hidden = [item for item in raw_candidates if item.tool.id not in selected_ids]
        st.caption("Ferramentas acionadas pelas regras, mas removidas da saída principal para manter o pacote enxuto.")
        if hidden:
            st.dataframe(_tools_dataframe(engine, hidden), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma ferramenta oculta.")

    with tabs[6]:
        render_go_no_go(engine)

    st.header("Relatório e Downloads")
    report = engine.generate_report(selected)
    json_data = engine.export_json_string(selected)
    csv_buffer = StringIO()
    _tools_dataframe(engine, selected).to_csv(csv_buffer, index=False, sep=";")

    with st.expander("Prévia do relatório consolidado", expanded=False):
        st.text_area("Relatório", report, height=500)

    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button(
            label="📄 Baixar relatório TXT",
            data=report.encode("utf-8"),
            file_name="relatorio_conceito.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            label="📦 Baixar JSON",
            data=json_data.encode("utf-8"),
            file_name="relatorio_conceito.json",
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


def render_tool_cards_by_gate(engine: MedConceptEngine, items: list[SelectedTool]) -> None:
    if not items:
        st.info("Nenhuma ferramenta selecionada.")
        return

    by_gate: dict[int, list[SelectedTool]] = {}
    for item in items:
        by_gate.setdefault(engine.tool_gate(item.tool.id), []).append(item)

    for gate in sorted(by_gate):
        st.subheader(engine.tool_gate_label(by_gate[gate][0].tool.id))
        render_tool_cards(by_gate[gate])


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
                st.markdown(f"**{item.tool.name}**")
                st.write(item.tool.description)
                if item.tool.subtools:
                    st.caption("Subferramentas: " + ", ".join(item.tool.subtools))
                st.caption(f"Justificativa: {item.reason}")


def render_go_no_go(engine: MedConceptEngine) -> None:
    for gate in range(1, 6):
        matrix = engine.gate_matrix(gate)
        st.subheader(f"Matriz Go/No-Go — Gate {gate}")
        st.caption(engine.tool_gate_label(f"G{gate}_"))
        st.dataframe(pd.DataFrame(matrix["rows"]), use_container_width=True, hide_index=True)
        decision = matrix["decision"]
        if decision.startswith("Go"):
            st.success(f"Decisão: {decision}")
        elif decision == "Revisar":
            st.warning("Decisão: Revisar")
        elif decision == "Pausar":
            st.info("Decisão: Pausar")
        else:
            st.error("Decisão: No-Go")
