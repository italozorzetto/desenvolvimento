"""
SISTEMA PARA GERAÇÃO DE CONCEITOS DE DISPOSITIVOS MÉDICOS — v6
Motor adaptativo para ciclo de idealização até conceito final aprovado.

Escopo:
    Gate 1 — Oportunidade e Necessidade
    Gate 2 — Estratégia Conceitual e Requisitos de Alto Nível
    Gate 3 — Geração de Alternativas
    Gate 4 — Seleção e Teste do Conceito
    Gate 5 — Conceito Final Aprovado

Princípios da v6:
    1. Não entra em projeto detalhado.
    2. Não usa FMEA, GR formal, validação, DFM formal ou especificação final.
    3. Usa triagens conceituais para temas regulatórios, fornecedor, manufatura e risco.
    4. Mantém biblioteca ampla, mas recomenda pacote inteligente por perfil.
    5. Produtos simples usam poucas perguntas e poucas ferramentas.
    6. Produtos inovadores/classe alta usam mais perguntas e mais ferramentas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


# =============================================================================
# ENUMS
# =============================================================================

class ToolPriority(Enum):
    MANDATORY = "✅ Obrigatória"
    RECOMMENDED = "🔵 Recomendada"
    OPTIONAL = "⚪ Opcional"


class ToolCategory(Enum):
    OPPORTUNITY = "Oportunidade e Necessidade"
    STRATEGY = "Estratégia Conceitual"
    TRIAGE = "Triagens Conceituais"
    REQUIREMENTS = "Requisitos Conceituais"
    IDEATION = "Geração de Alternativas"
    SELECTION = "Seleção e Teste do Conceito"
    DELIVERABLES = "Entregáveis Conceituais"
    DECISION = "Go/No-Go"


class ComplexityLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    ULTRA = 4


class RegulatoryClass(Enum):
    UNKNOWN = 0
    CLASS_I = 1
    CLASS_II = 2
    CLASS_III = 3
    CLASS_IV = 4


# =============================================================================
# MODELOS DE DADOS
# =============================================================================

@dataclass
class ProjectProfile:
    # Identificação e estratégia
    project_origin: str = ""
    development_strategy: list[str] = field(default_factory=list)
    company_responsibility: list[str] = field(default_factory=list)

    # Produto / uso
    regulatory_class: RegulatoryClass = RegulatoryClass.UNKNOWN
    regulatory_class_known: bool = False
    has_patient_contact: bool = False
    invasiveness_level: int = 0
    sterility_required: bool = False
    sterility_unknown: bool = False
    has_digital_component: bool = False
    has_associated_drug: bool = False
    critical_use: bool = False
    user_type: str = ""
    multi_stakeholder: bool = False

    # Produto externo / fornecedor / rota produtiva conceitual
    supplier_dependency: str = ""
    has_multiple_suppliers: bool = False
    has_supplier_sample: bool = False
    manufacturing_strategy: str = ""
    likely_manufacturing_complexity: str = ""
    cost_is_critical: bool = False
    expected_volume: str = ""

    # Novidade, tecnologia e referência
    tech_maturity: int = 3
    has_existing_reference: bool = False
    reference_is_competitor: bool = False
    reference_is_own: bool = False
    has_similar_registration: bool = False
    has_market_benchmark: bool = False
    ip_uncertainty: bool = False

    # Regulatório conceitual / customização
    regulatory_uncertainty: str = ""
    labeling_change_required: bool = False
    ifu_change_required: bool = False
    packaging_change_required: bool = False
    norm_identified: bool = False
    claims_uncertain: bool = False

    # Necessidade / campo
    problem_clarity: int = 0
    need_evidence_level: int = 0
    has_field_observation: bool = False
    needs_internal_approval: bool = False
    timeline: str = ""

    # Controle
    concept_uncertainties: list[str] = field(default_factory=list)
    raw_answers: list[dict[str, Any]] = field(default_factory=list)
    complexity: ComplexityLevel = ComplexityLevel.LOW
    complexity_score: int = 0
    score_breakdown: dict[str, int] = field(default_factory=dict)

    def add_uncertainty(self, value: str) -> None:
        if value and value not in self.concept_uncertainties:
            self.concept_uncertainties.append(value)

    def remove_uncertainty(self, value: str) -> None:
        if value in self.concept_uncertainties:
            self.concept_uncertainties.remove(value)

    # ---------------------------------------------------------------------
    # Predicados de rota
    # ---------------------------------------------------------------------
    def is_oem(self) -> bool:
        return any(s in self.development_strategy for s in ["oem_pure", "white_label"])

    def is_white_label(self) -> bool:
        return "white_label" in self.development_strategy

    def is_resale_ready(self) -> bool:
        return "oem_pure" in self.development_strategy and not self.needs_concept_generation()

    def is_adaptation(self) -> bool:
        return any(s in self.development_strategy for s in [
            "doc_adaptation", "tech_adaptation", "material_change", "process_change", "labeling_change"
        ])

    def is_supplier_change(self) -> bool:
        return "supplier_change" in self.development_strategy

    def is_inhouse(self) -> bool:
        return any(s in self.development_strategy for s in ["inhouse_production", "nationalization"])

    def is_kit_or_accessory(self) -> bool:
        return any(s in self.development_strategy for s in ["new_kit", "new_accessory"])

    def is_product_similar(self) -> bool:
        return "similar_competitor" in self.development_strategy

    def is_innovation(self) -> bool:
        return any(s in self.development_strategy for s in [
            "incremental_innovation", "radical_innovation", "platform"
        ])

    def is_radical(self) -> bool:
        return "radical_innovation" in self.development_strategy

    def is_platform(self) -> bool:
        return "platform" in self.development_strategy

    def has_external_supplier(self) -> bool:
        return self.supplier_dependency in ["external_defined", "external_undefined"]

    def is_reference_based(self) -> bool:
        return any(s in self.development_strategy for s in [
            "similar_competitor", "doc_adaptation", "tech_adaptation", "material_change",
            "supplier_change", "nationalization", "new_kit", "new_accessory", "oem_pure", "white_label"
        ])

    def needs_concept_generation(self) -> bool:
        return any(s in self.development_strategy for s in [
            "incremental_innovation", "radical_innovation", "platform", "new_kit",
            "new_accessory", "similar_competitor", "tech_adaptation"
        ])

    def complexity_gte(self, level: ComplexityLevel) -> bool:
        return self.complexity.value >= level.value

    def is_class_high(self) -> bool:
        return self.regulatory_class.value >= RegulatoryClass.CLASS_III.value

    def is_class_iv(self) -> bool:
        return self.regulatory_class == RegulatoryClass.CLASS_IV

    def is_simple_project(self) -> bool:
        simple_strategy = set(self.development_strategy) <= {"oem_pure", "white_label", "doc_adaptation"}
        class_ok = self.regulatory_class in [RegulatoryClass.UNKNOWN, RegulatoryClass.CLASS_I, RegulatoryClass.CLASS_II]
        return simple_strategy and class_ok and not self.has_patient_contact and not self.sterility_required

    def is_fast_track_resale(self) -> bool:
        return (
            self.is_resale_ready()
            and self.regulatory_class == RegulatoryClass.CLASS_I
            and not self.sterility_required
            and not self.has_patient_contact
            and self.supplier_dependency != "external_undefined"
        )

    def compute_complexity(self) -> ComplexityLevel:
        bd: dict[str, int] = {}
        bd["Classe regulatória"] = max(0, self.regulatory_class.value - 1) * 3
        bd["Invasividade"] = self.invasiveness_level * 3
        bd["Maturidade tecnológica"] = max(0, 3 - self.tech_maturity) * 2
        bd["Clareza do problema"] = max(0, 2 - self.problem_clarity) * 2
        bd["Evidência da necessidade"] = max(0, 2 - self.need_evidence_level) * 2
        bd["Multi-stakeholder"] = int(self.multi_stakeholder) * 2
        bd["Componente digital"] = int(self.has_digital_component) * 2
        bd["Esterilidade"] = int(self.sterility_required or self.sterility_unknown) * 2
        bd["Medicamento/fluido associado"] = int(self.has_associated_drug) * 3
        bd["Uso crítico"] = int(self.critical_use) * 2
        bd["Incerteza regulatória"] = {"": 0, "low": 1, "medium": 2, "high": 3}.get(self.regulatory_uncertainty, 0) * 2
        bd["Incertezas do conceito"] = len(self.concept_uncertainties)
        bd["Fornecedor indefinido"] = int(self.supplier_dependency == "external_undefined") * 2
        bd["Inovação radical"] = int(self.is_radical()) * 4
        bd["Plataforma"] = int(self.is_platform()) * 3
        bd["IP incerto"] = int(self.ip_uncertainty) * 2
        bd["Manufatura conceitual complexa"] = int(self.likely_manufacturing_complexity == "high") * 2

        self.score_breakdown = bd
        self.complexity_score = sum(bd.values())

        if self.complexity_score <= 7:
            self.complexity = ComplexityLevel.LOW
        elif self.complexity_score <= 16:
            self.complexity = ComplexityLevel.MEDIUM
        elif self.complexity_score <= 28:
            self.complexity = ComplexityLevel.HIGH
        else:
            self.complexity = ComplexityLevel.ULTRA
        return self.complexity


@dataclass
class Tool:
    id: str
    name: str
    category: ToolCategory
    description: str
    subtools: list[str] = field(default_factory=list)


@dataclass
class ToolRule:
    tool_id: str
    condition: Callable[[ProjectProfile], bool]
    priority_fn: Callable[[ProjectProfile], ToolPriority]
    reason_fn: Callable[[ProjectProfile], str]


@dataclass
class SelectedTool:
    tool: Tool
    priority: ToolPriority
    reason: str


@dataclass
class Question:
    id: str
    text: str
    options: dict[str, str]
    handler: Callable[[str | list[str], ProjectProfile], list[str]]
    multiple: bool = False
    exclusive_options: set[str] = field(default_factory=set)
    help_text: str = ""


# =============================================================================
# BIBLIOTECA DE FERRAMENTAS — SOMENTE CONCEITO
# =============================================================================

def T(id_: str, name: str, cat: ToolCategory, desc: str, subs: list[str] | None = None) -> Tool:
    return Tool(id_, name, cat, desc, subs or [])


TOOL_LIBRARY: dict[str, Tool] = {t.id: t for t in [
    # Gate 1 — Oportunidade e Necessidade
    T("G1_OPP01", "Declaração da oportunidade", ToolCategory.OPPORTUNITY,
      "Descrever problema, origem, contexto e hipótese inicial da oportunidade."),
    T("G1_OPP02", "5W2H da oportunidade", ToolCategory.OPPORTUNITY,
      "Organizar as informações básicas da ideia sem fechar solução."),
    T("G1_STK01", "Mapa de stakeholders", ToolCategory.OPPORTUNITY,
      "Identificar usuários, clientes, pacientes, compradores e influenciadores."),
    T("G1_VOC01", "VOC inicial", ToolCategory.OPPORTUNITY,
      "Capturar percepções iniciais de usuários, clientes ou áreas internas.",
      ["Feedbacks", "questionário simples", "reclamações", "demandas comerciais"]),
    T("G1_KOL01", "Entrevistas com usuários/KOL", ToolCategory.OPPORTUNITY,
      "Validar dor clínica, técnica, operacional ou comercial com pessoas-chave."),
    T("G1_OBS01", "Observação em campo", ToolCategory.OPPORTUNITY,
      "Entender o contexto real de uso sem propor projeto definitivo."),
    T("G1_GAP01", "Gap Analysis", ToolCategory.OPPORTUNITY,
      "Comparar situação atual, necessidade não atendida e estado desejado."),
    T("G1_BEN01", "Benchmarking preliminar", ToolCategory.OPPORTUNITY,
      "Identificar soluções, produtos, métodos ou alternativas existentes."),
    T("G1_VAL01", "Proposta de valor inicial", ToolCategory.OPPORTUNITY,
      "Definir benefício esperado, dor atendida e diferencial preliminar."),
    T("G1_RVV01", "Real, Vencível, Vale a pena", ToolCategory.OPPORTUNITY,
      "Avaliar se a oportunidade parece real, competitiva e justificável."),
    T("G1_UNC01", "Mapa inicial de incertezas", ToolCategory.OPPORTUNITY,
      "Registrar dúvidas técnicas, clínicas, regulatórias, comerciais e econômicas."),
    T("G1_GO01", "Matriz Go/No-Go — Gate 1", ToolCategory.DECISION,
      "Decidir se a oportunidade deve avançar para estratégia conceitual."),

    # Gate 2 — Estratégia Conceitual e Requisitos de Alto Nível
    T("G2_STR01", "Classificação da rota de desenvolvimento", ToolCategory.STRATEGY,
      "Classificar OEM, adaptação, kit, similar, internalização ou inovação."),
    T("G2_NEED01", "Lista de necessidades do usuário", ToolCategory.REQUIREMENTS,
      "Consolidar necessidades do usuário em linguagem clara e não técnica."),
    T("G2_NEED02", "Priorização de necessidades", ToolCategory.REQUIREMENTS,
      "Priorizar necessidades por importância, frequência, criticidade e valor."),
    T("G2_USE01", "Uso pretendido preliminar", ToolCategory.REQUIREMENTS,
      "Definir finalidade clínica inicial sem fechar especificação de projeto."),
    T("G2_USE02", "Perfil de usuário e ambiente", ToolCategory.REQUIREMENTS,
      "Identificar quem usa, onde usa e em qual contexto."),
    T("G2_QFD01", "QFD conceitual — nível 1", ToolCategory.REQUIREMENTS,
      "Traduzir necessidades em requisitos conceituais e direcionadores iniciais.",
      ["Voz do cliente", "necessidades priorizadas", "direcionadores de conceito", "relações fortes/médias/fracas"]),
    T("G2_CTQ01", "CTQ preliminar", ToolCategory.REQUIREMENTS,
      "Identificar atributos críticos que devem orientar a geração de conceitos."),
    T("G2_OEM01", "Triagem OEM / produto de mercado", ToolCategory.TRIAGE,
      "Verificar se um produto pronto pode atender à oportunidade."),
    T("G2_SUP01", "Triagem de fornecedor externo", ToolCategory.TRIAGE,
      "Identificar dependência, maturidade e incertezas de fornecedor.",
      ["Fornecedor definido", "fornecedor indefinido", "amostra comercial", "documentação a solicitar futuramente"]),
    T("G2_CUS01", "Triagem de customização", ToolCategory.TRIAGE,
      "Identificar se haverá alteração de marca, IFU, rotulagem, embalagem ou uso."),
    T("G2_SIM01", "Triagem de produto similar", ToolCategory.TRIAGE,
      "Avaliar referência existente, produto concorrente ou método padrão."),
    T("G2_KIT01", "Triagem de kit ou acessório", ToolCategory.TRIAGE,
      "Identificar impactos conceituais de composição, compatibilidade e apresentação."),
    T("G2_INT01", "Triagem de internalização/nacionalização", ToolCategory.TRIAGE,
      "Identificar intenção de fabricar, nacionalizar ou internalizar no futuro."),
    T("G2_REG01", "Triagem regulatória preliminar", ToolCategory.TRIAGE,
      "Identificar classe provável, incertezas e alertas regulatórios iniciais."),
    T("G2_PAT01", "Triagem de contato com paciente", ToolCategory.TRIAGE,
      "Classificar contato, invasividade, duração e criticidade de uso."),
    T("G2_STE01", "Triagem de esterilidade", ToolCategory.TRIAGE,
      "Identificar se esterilidade é requisito provável ou incerteza relevante."),
    T("G2_USECRIT01", "Triagem de uso crítico", ToolCategory.TRIAGE,
      "Identificar tarefas críticas, erro previsível e necessidade de treinamento."),
    T("G2_PROD01", "Triagem produtiva conceitual", ToolCategory.TRIAGE,
      "Identificar rota produtiva provável sem realizar DFM ou processo final."),
    T("G2_ECO01", "Triagem econômica preliminar", ToolCategory.TRIAGE,
      "Identificar se custo, volume, preço-alvo ou importação são críticos."),
    T("G2_SEARCH01", "Busca externa de soluções", ToolCategory.STRATEGY,
      "Buscar referências externas para apoiar a rota conceitual.",
      ["Benchmarking", "Patent Mapping", "FTO preliminar", "literatura", "fornecedores", "produtos similares"]),
    T("G2_UNC01", "Mapa atualizado de incertezas", ToolCategory.STRATEGY,
      "Consolidar alertas identificados após as triagens conceituais."),
    T("G2_LRN01", "Plano de aprendizagem do conceito", ToolCategory.STRATEGY,
      "Definir o que precisa ser aprendido antes de aprovar o conceito."),
    T("G2_GO01", "Matriz Go/No-Go — Gate 2", ToolCategory.DECISION,
      "Decidir se a estratégia conceitual está adequada."),

    # Gate 3 — Geração de Alternativas
    T("G3_INTSEARCH01", "Busca interna de soluções", ToolCategory.IDEATION,
      "Explorar produtos internos, projetos antigos, know-how e aprendizados."),
    T("G3_EXTSEARCH01", "Busca externa de soluções", ToolCategory.IDEATION,
      "Explorar soluções externas para inspirar alternativas de conceito.",
      ["Benchmarking", "patentes", "literatura", "fornecedores", "produtos análogos"]),
    T("G3_MIND01", "Mapa mental", ToolCategory.IDEATION,
      "Organizar ideias, caminhos, conexões, restrições e oportunidades."),
    T("G3_FUNC01", "Decomposição funcional", ToolCategory.IDEATION,
      "Separar função global, subfunções, entradas e saídas do produto."),
    T("G3_BRAIN01", "Brainstorming estruturado", ToolCategory.IDEATION,
      "Gerar alternativas de solução orientadas pela necessidade."),
    T("G3_SCAMPER01", "SCAMPER", ToolCategory.IDEATION,
      "Adaptar soluções por substituir, combinar, adaptar, modificar e reorganizar."),
    T("G3_TRIZ01", "TRIZ conceitual", ToolCategory.IDEATION,
      "Resolver contradições técnicas iniciais sem congelar projeto."),
    T("G3_MORPH01", "Matriz morfológica", ToolCategory.IDEATION,
      "Combinar subfunções e princípios de solução para gerar conceitos."),
    T("G3_TREE01", "Árvore de classificação de conceitos", ToolCategory.IDEATION,
      "Organizar famílias e rotas de solução conceitual."),
    T("G3_COMBO01", "Tabela de combinação de conceitos", ToolCategory.IDEATION,
      "Combinar alternativas promissoras derivadas da matriz morfológica."),
    T("G3_SKETCH01", "Sketch conceitual", ToolCategory.IDEATION,
      "Representar visualmente alternativas iniciais do conceito."),
    T("G3_STORY01", "Storyboard de uso", ToolCategory.IDEATION,
      "Mostrar a sequência de uso e interação do conceito."),
    T("G3_PROTO01", "Prototipagem conceitual simples", ToolCategory.IDEATION,
      "Tangibilizar ideias sem validar ou congelar projeto."),
    T("G3_POP01", "Prova de princípio simples", ToolCategory.IDEATION,
      "Testar possibilidade básica do princípio, sem verificação formal."),
    T("G3_GO01", "Matriz Go/No-Go — Gate 3", ToolCategory.DECISION,
      "Decidir se existem alternativas suficientes para seleção."),

    # Gate 4 — Seleção e Teste do Conceito
    T("G4_CRIT01", "Critérios de seleção do conceito", ToolCategory.SELECTION,
      "Definir critérios antes de comparar alternativas."),
    T("G4_REF01", "Conceito de referência", ToolCategory.SELECTION,
      "Definir produto atual, concorrente ou método padrão para comparação."),
    T("G4_SCREEN01", "Matriz de triagem de conceitos", ToolCategory.SELECTION,
      "Filtrar alternativas rapidamente antes de análise mais detalhada."),
    T("G4_PUGH01", "Matriz de Pugh", ToolCategory.SELECTION,
      "Comparar conceitos contra referência por critérios qualitativos."),
    T("G4_WEIGHT01", "Matriz de decisão ponderada", ToolCategory.SELECTION,
      "Selecionar conceito por pesos, notas e pontuação total."),
    T("G4_TRADE01", "Trade-off conceitual", ToolCategory.SELECTION,
      "Comparar ganhos, perdas, incertezas e impactos entre alternativas."),
    T("G4_NEEDCON01", "Matriz necessidade × conceito", ToolCategory.SELECTION,
      "Verificar aderência das alternativas às necessidades priorizadas."),
    T("G4_CTQCON01", "Matriz CTQ × conceito", ToolCategory.SELECTION,
      "Verificar aderência das alternativas aos CTQs preliminares."),
    T("G4_ATTR01", "Atratividade do conceito", ToolCategory.SELECTION,
      "Avaliar clareza, valor percebido, adoção e diferencial."),
    T("G4_TEST01", "Teste de conceito preliminar", ToolCategory.SELECTION,
      "Avaliar entendimento e aceitação com usuário ou especialista."),
    T("G4_PROTO01", "Prototipagem conceitual de apoio", ToolCategory.SELECTION,
      "Apoiar comunicação, teste e comparação do conceito."),
    T("G4_SCORE01", "Scorecard de conceito", ToolCategory.SELECTION,
      "Consolidar avaliação final da alternativa escolhida."),
    T("G4_UNC01", "Mapa de incertezas do conceito selecionado", ToolCategory.SELECTION,
      "Registrar dúvidas remanescentes do conceito selecionado."),
    T("G4_GO01", "Matriz Go/No-Go — Gate 4", ToolCategory.DECISION,
      "Decidir se o conceito selecionado pode ser consolidado."),

    # Gate 5 — Conceito Final Aprovado
    T("G5_MISSION01", "Declaração de missão do conceito", ToolCategory.DELIVERABLES,
      "Consolidar objetivo, mercado, usuário, benefício e fronteiras do conceito."),
    T("G5_REQ01", "Requisitos conceituais preliminares", ToolCategory.DELIVERABLES,
      "Consolidar requisitos de alto nível sem especificação final."),
    T("G5_UNS01", "User Needs Statement", ToolCategory.DELIVERABLES,
      "Formalizar necessidades do usuário em formato claro e rastreável."),
    T("G5_CTQ01", "CTQ consolidado do conceito", ToolCategory.DELIVERABLES,
      "Registrar CTQs escolhidos para orientar o projeto posterior."),
    T("G5_QFD01", "QFD conceitual consolidado", ToolCategory.DELIVERABLES,
      "Registrar relação necessidade × requisito conceitual, se aplicável."),
    T("G5_CLAIMS01", "Claims pretendidos", ToolCategory.DELIVERABLES,
      "Registrar alegações desejadas e evidências futuras necessárias."),
    T("G5_UNC01", "Mapa final de incertezas", ToolCategory.DELIVERABLES,
      "Consolidar incertezas que o time de projeto deverá aprofundar."),
    T("G5_LRN01", "Plano de aprendizagem para projeto", ToolCategory.DELIVERABLES,
      "Indicar o que deve ser investigado na próxima fase."),
    T("G5_PREM01", "Premissas e restrições do conceito", ToolCategory.DELIVERABLES,
      "Registrar hipóteses, limites e condições assumidas no conceito."),
    T("G5_RECOM01", "Recomendações para próxima fase", ToolCategory.DELIVERABLES,
      "Orientar o time de projeto sem executar projeto detalhado."),
    T("G5_ONEPAGE01", "One-Page Concept", ToolCategory.DELIVERABLES,
      "Resumir o conceito aprovado em uma página."),
    T("G5_REPORT01", "Relatório final de conceito", ToolCategory.DELIVERABLES,
      "Consolidar os relatórios dos gates e a decisão final."),
    T("G5_TERM01", "Termo de conceito aprovado", ToolCategory.DELIVERABLES,
      "Formalizar aprovação do conceito para transferência."),
    T("G5_TRANSFER01", "Pacote de transferência conceitual", ToolCategory.DELIVERABLES,
      "Entregar decisões, premissas, incertezas e recomendações ao projeto."),
    T("G5_GO01", "Matriz Go/No-Go — Gate 5", ToolCategory.DECISION,
      "Decidir se o conceito final está aprovado para projeto."),
]}


# =============================================================================
# REGRAS
# =============================================================================

def _prio(mandatory_if: Callable[[ProjectProfile], bool], p: ProjectProfile) -> ToolPriority:
    return ToolPriority.MANDATORY if mandatory_if(p) else ToolPriority.RECOMMENDED


def _simple_prio(mandatory_if: Callable[[ProjectProfile], bool], p: ProjectProfile) -> ToolPriority:
    if p.is_fast_track_resale() or p.is_simple_project():
        return ToolPriority.OPTIONAL
    return ToolPriority.MANDATORY if mandatory_if(p) else ToolPriority.RECOMMENDED


def _always(_: ProjectProfile) -> bool:
    return True


RULES: list[ToolRule] = [
    # Go/No-Go em todos os Gates
    *[
        ToolRule(tid, _always, lambda p: ToolPriority.MANDATORY,
                 lambda p, tid=tid: f"Matriz obrigatória de decisão do {TOOL_LIBRARY[tid].name.split('—')[-1].strip()}.")
        for tid in ["G1_GO01", "G2_GO01", "G3_GO01", "G4_GO01", "G5_GO01"]
    ],

    # Gate 1
    ToolRule("G1_OPP01", _always, lambda p: ToolPriority.MANDATORY,
             lambda p: "Toda análise conceitual deve começar pela declaração da oportunidade."),
    ToolRule("G1_OPP02", lambda p: not p.is_fast_track_resale(), lambda p: ToolPriority.RECOMMENDED,
             lambda p: "5W2H organiza a oportunidade antes de aprofundar o conceito."),
    ToolRule("G1_STK01", lambda p: p.multi_stakeholder or p.is_innovation() or p.has_patient_contact,
             lambda p: _prio(lambda x: x.multi_stakeholder or x.is_class_high(), p),
             lambda p: "Dispositivo médico pode envolver vários stakeholders; mapa ajuda a delimitar contexto."),
    ToolRule("G1_VOC01", lambda p: p.is_innovation() or p.problem_clarity < 2 or p.need_evidence_level < 2,
             lambda p: _prio(lambda x: x.is_innovation() or x.problem_clarity == 0, p),
             lambda p: "VOC ajuda a confirmar necessidade antes de gerar conceito."),
    ToolRule("G1_KOL01", lambda p: p.is_innovation() or p.invasiveness_level >= 2 or p.is_class_high(),
             lambda p: _prio(lambda x: x.is_class_high() or x.is_radical(), p),
             lambda p: "Especialista clínico ajuda a validar relevância da necessidade."),
    ToolRule("G1_OBS01", lambda p: (p.is_innovation() or p.critical_use) and not p.has_field_observation,
             lambda p: _prio(lambda x: x.is_radical() or x.critical_use, p),
             lambda p: "Observação em campo reduz incerteza sobre contexto real de uso."),
    ToolRule("G1_GAP01", lambda p: p.problem_clarity < 2 or p.is_innovation(),
             lambda p: _prio(lambda x: x.problem_clarity == 0, p),
             lambda p: "Gap Analysis estrutura a diferença entre situação atual e desejada."),
    ToolRule("G1_BEN01", lambda p: p.is_oem() or p.is_reference_based() or p.is_innovation(),
             lambda p: _prio(lambda x: x.is_oem() or x.is_product_similar(), p),
             lambda p: "Benchmarking preliminar é necessário para entender soluções existentes."),
    ToolRule("G1_VAL01", _always, lambda p: _simple_prio(lambda x: not x.is_simple_project(), p),
             lambda p: "Proposta de valor define benefício esperado do conceito."),
    ToolRule("G1_RVV01", lambda p: not p.is_fast_track_resale() or p.cost_is_critical,
             lambda p: _prio(lambda x: x.cost_is_critical or x.is_innovation(), p),
             lambda p: "Real, Vencível, Vale a pena apoia decisão inicial de avançar."),
    ToolRule("G1_UNC01", lambda p: len(p.concept_uncertainties) > 0 or not p.is_fast_track_resale(),
             lambda p: _prio(lambda x: len(x.concept_uncertainties) >= 2 or x.is_innovation(), p),
             lambda p: "Mapa de incertezas evita bloquear o conceito cedo demais."),

    # Gate 2
    ToolRule("G2_STR01", _always, lambda p: ToolPriority.MANDATORY,
             lambda p: "A rota de desenvolvimento define como o pacote de ferramentas será montado."),
    ToolRule("G2_NEED01", lambda p: p.is_innovation() or p.problem_clarity < 2 or p.has_patient_contact,
             lambda p: _prio(lambda x: x.is_innovation(), p),
             lambda p: "Lista de necessidades orienta QFD, CTQ e geração de alternativas."),
    ToolRule("G2_NEED02", lambda p: p.is_innovation() or p.multi_stakeholder or p.need_evidence_level < 2,
             lambda p: _prio(lambda x: x.is_radical() or x.multi_stakeholder, p),
             lambda p: "Priorização evita gerar conceitos desalinhados à necessidade principal."),
    ToolRule("G2_USE01", _always, lambda p: _simple_prio(lambda x: x.has_patient_contact or x.is_innovation(), p),
             lambda p: "Uso pretendido preliminar define a fronteira conceitual do produto."),
    ToolRule("G2_USE02", lambda p: p.user_type or p.has_patient_contact or p.is_innovation(),
             lambda p: _simple_prio(lambda x: x.multi_stakeholder or x.has_patient_contact, p),
             lambda p: "Perfil de usuário e ambiente orienta o contexto de uso."),
    ToolRule("G2_QFD01", lambda p: p.is_innovation() or p.is_class_high() or p.multi_stakeholder or p.need_evidence_level < 2,
             lambda p: _prio(lambda x: x.is_radical() or x.is_class_high(), p),
             lambda p: "QFD conceitual traduz necessidades em direcionadores de conceito."),
    ToolRule("G2_CTQ01", lambda p: p.is_innovation() or p.complexity_gte(ComplexityLevel.MEDIUM) or p.has_patient_contact,
             lambda p: _prio(lambda x: x.is_radical() or x.is_class_high(), p),
             lambda p: "CTQ preliminar deve orientar a geração de alternativas."),
    ToolRule("G2_OEM01", lambda p: p.is_oem(), lambda p: ToolPriority.MANDATORY,
             lambda p: "Produto comprado ou white label exige triagem conceitual OEM."),
    ToolRule("G2_SUP01", lambda p: p.has_external_supplier() or p.is_supplier_change(),
             lambda p: _prio(lambda x: x.supplier_dependency == "external_undefined" or x.is_supplier_change(), p),
             lambda p: "Fornecedor externo deve ser tratado como dependência conceitual, não qualificação formal."),
    ToolRule("G2_CUS01", lambda p: p.labeling_change_required or p.ifu_change_required or p.packaging_change_required or p.is_white_label(),
             lambda p: ToolPriority.MANDATORY,
             lambda p: "Na fase de conceito, a customização é apenas identificada, não definida."),
    ToolRule("G2_SIM01", lambda p: p.is_product_similar() or p.has_existing_reference or p.has_similar_registration,
             lambda p: _prio(lambda x: x.is_product_similar(), p),
             lambda p: "Produto similar ou referência exige triagem conceitual de equivalência."),
    ToolRule("G2_KIT01", lambda p: p.is_kit_or_accessory(), lambda p: ToolPriority.MANDATORY,
             lambda p: "Kit ou acessório exige triagem de composição e impacto conceitual."),
    ToolRule("G2_INT01", lambda p: p.is_inhouse(), lambda p: ToolPriority.MANDATORY,
             lambda p: "Internalização/nacionalização é tratada como intenção e incerteza conceitual."),
    ToolRule("G2_REG01", lambda p: not p.regulatory_class_known or p.regulatory_class.value >= 2 or p.regulatory_uncertainty in ["medium", "high"],
             lambda p: _prio(lambda x: not x.regulatory_class_known or x.is_class_high(), p),
             lambda p: "Triagem regulatória preliminar evita seguir sem entender o risco regulatório."),
    ToolRule("G2_PAT01", lambda p: p.has_patient_contact or p.invasiveness_level > 0,
             lambda p: _prio(lambda x: x.invasiveness_level >= 2, p),
             lambda p: "Contato com paciente influencia requisitos conceituais e incertezas futuras."),
    ToolRule("G2_STE01", lambda p: p.sterility_required or p.sterility_unknown,
             lambda p: _prio(lambda x: x.sterility_required, p),
             lambda p: "Esterilidade é tratada como alerta conceitual, não validação."),
    ToolRule("G2_USECRIT01", lambda p: p.critical_use or p.user_type in ["patient_or_caregiver", "multiple_users"],
             lambda p: _prio(lambda x: x.critical_use, p),
             lambda p: "Uso crítico deve ser registrado como incerteza para o projeto."),
    ToolRule("G2_PROD01", lambda p: p.is_inhouse() or p.likely_manufacturing_complexity or "manufacturing" in p.concept_uncertainties,
             lambda p: _prio(lambda x: x.likely_manufacturing_complexity == "high", p),
             lambda p: "Triagem produtiva identifica rota provável sem fazer DFM."),
    ToolRule("G2_ECO01", lambda p: p.cost_is_critical or p.expected_volume or p.is_oem() or p.is_inhouse(),
             lambda p: _prio(lambda x: x.cost_is_critical, p),
             lambda p: "Triagem econômica indica se custo pode ser impeditivo."),
    ToolRule("G2_SEARCH01", lambda p: p.is_reference_based() or p.is_innovation() or p.ip_uncertainty,
             lambda p: _prio(lambda x: x.is_radical() or x.ip_uncertainty or x.is_product_similar(), p),
             lambda p: "Busca externa reúne benchmarking, patentes e FTO preliminar."),
    ToolRule("G2_UNC01", lambda p: len(p.concept_uncertainties) > 0 or p.complexity_gte(ComplexityLevel.MEDIUM),
             lambda p: _prio(lambda x: x.complexity_gte(ComplexityLevel.HIGH), p),
             lambda p: "Incertezas atualizadas orientam próximos gates."),
    ToolRule("G2_LRN01", lambda p: len(p.concept_uncertainties) > 0 or p.is_innovation(),
             lambda p: _prio(lambda x: x.is_radical() or len(x.concept_uncertainties) >= 3, p),
             lambda p: "Plano de aprendizagem define o que deve ser aprendido antes do projeto."),

    # Gate 3
    ToolRule("G3_INTSEARCH01", lambda p: p.needs_concept_generation() or p.is_innovation(),
             lambda p: _prio(lambda x: x.is_innovation(), p),
             lambda p: "Busca interna evita perder conhecimento já existente."),
    ToolRule("G3_EXTSEARCH01", lambda p: p.needs_concept_generation() or p.is_reference_based(),
             lambda p: _prio(lambda x: x.is_product_similar() or x.is_innovation(), p),
             lambda p: "Busca externa inspira alternativas sem limitar a solução."),
    ToolRule("G3_MIND01", lambda p: p.needs_concept_generation(), lambda p: ToolPriority.RECOMMENDED,
             lambda p: "Mapa mental organiza alternativas e caminhos."),
    ToolRule("G3_FUNC01", lambda p: p.needs_concept_generation() or p.is_innovation(),
             lambda p: _prio(lambda x: x.is_radical() or x.complexity_gte(ComplexityLevel.HIGH), p),
             lambda p: "Decomposição funcional orienta conceitos pela função, não pela forma."),
    ToolRule("G3_BRAIN01", lambda p: p.needs_concept_generation(), lambda p: ToolPriority.MANDATORY,
             lambda p: "Geração de alternativas exige brainstorming estruturado."),
    ToolRule("G3_SCAMPER01", lambda p: p.is_adaptation() or p.is_kit_or_accessory() or "incremental_innovation" in p.development_strategy,
             lambda p: ToolPriority.RECOMMENDED,
             lambda p: "SCAMPER é útil para adaptação, melhoria e kit/acessório."),
    ToolRule("G3_TRIZ01", lambda p: p.is_radical() or p.complexity_gte(ComplexityLevel.HIGH),
             lambda p: _prio(lambda x: x.is_radical(), p),
             lambda p: "TRIZ apoia contradições técnicas em conceitos complexos."),
    ToolRule("G3_MORPH01", lambda p: p.needs_concept_generation() and p.complexity_gte(ComplexityLevel.MEDIUM),
             lambda p: _prio(lambda x: x.is_radical() or x.is_platform(), p),
             lambda p: "Matriz morfológica combina subfunções em alternativas."),
    ToolRule("G3_TREE01", lambda p: p.needs_concept_generation() and (p.is_innovation() or p.complexity_gte(ComplexityLevel.MEDIUM)),
             lambda p: ToolPriority.RECOMMENDED,
             lambda p: "Árvore organiza famílias de conceitos."),
    ToolRule("G3_COMBO01", lambda p: p.needs_concept_generation() and p.complexity_gte(ComplexityLevel.MEDIUM),
             lambda p: ToolPriority.RECOMMENDED,
             lambda p: "Tabela de combinação transforma opções em conceitos candidatos."),
    ToolRule("G3_SKETCH01", lambda p: p.needs_concept_generation(), lambda p: ToolPriority.RECOMMENDED,
             lambda p: "Sketch comunica alternativas de forma simples."),
    ToolRule("G3_STORY01", lambda p: p.needs_concept_generation() and (p.critical_use or p.user_type != ""),
             lambda p: ToolPriority.RECOMMENDED,
             lambda p: "Storyboard ajuda a visualizar uso e interação."),
    ToolRule("G3_PROTO01", lambda p: p.needs_concept_generation() and p.complexity_gte(ComplexityLevel.MEDIUM),
             lambda p: ToolPriority.RECOMMENDED,
             lambda p: "Protótipo conceitual tangibiliza alternativas sem validar produto."),
    ToolRule("G3_POP01", lambda p: p.is_innovation() and ("technology" in p.concept_uncertainties or p.tech_maturity <= 2),
             lambda p: _prio(lambda x: x.tech_maturity <= 1, p),
             lambda p: "Prova de princípio reduz incerteza técnica inicial."),

    # Gate 4
    ToolRule("G4_CRIT01", lambda p: p.needs_concept_generation() or p.is_adaptation() or p.is_product_similar(),
             lambda p: ToolPriority.MANDATORY,
             lambda p: "Critérios devem ser definidos antes de selecionar conceito."),
    ToolRule("G4_REF01", lambda p: p.has_existing_reference or p.is_product_similar() or p.is_oem(),
             lambda p: _prio(lambda x: x.is_product_similar(), p),
             lambda p: "Conceito de referência torna a comparação mais objetiva."),
    ToolRule("G4_SCREEN01", lambda p: p.needs_concept_generation(), lambda p: ToolPriority.RECOMMENDED,
             lambda p: "Triagem de conceitos filtra alternativas antes da matriz final."),
    ToolRule("G4_PUGH01", lambda p: p.needs_concept_generation() or p.is_adaptation() or p.is_inhouse(),
             lambda p: _prio(lambda x: x.complexity_gte(ComplexityLevel.MEDIUM), p),
             lambda p: "Pugh compara alternativas contra referência."),
    ToolRule("G4_WEIGHT01", lambda p: p.needs_concept_generation() and p.complexity_gte(ComplexityLevel.MEDIUM),
             lambda p: _prio(lambda x: x.complexity_gte(ComplexityLevel.HIGH), p),
             lambda p: "Matriz ponderada apoia decisão quando há vários critérios."),
    ToolRule("G4_TRADE01", lambda p: p.needs_concept_generation() or p.complexity_gte(ComplexityLevel.MEDIUM),
             lambda p: ToolPriority.RECOMMENDED,
             lambda p: "Trade-off conceitual explicita ganhos, perdas e incertezas."),
    ToolRule("G4_NEEDCON01", lambda p: p.needs_concept_generation() or p.is_innovation(),
             lambda p: _prio(lambda x: x.is_innovation(), p),
             lambda p: "Matriz necessidade × conceito verifica aderência às necessidades."),
    ToolRule("G4_CTQCON01", lambda p: p.is_innovation() or p.complexity_gte(ComplexityLevel.MEDIUM) or p.has_patient_contact,
             lambda p: _prio(lambda x: x.is_class_high() or x.is_radical(), p),
             lambda p: "Matriz CTQ × conceito verifica aderência aos atributos críticos."),
    ToolRule("G4_ATTR01", _always, lambda p: _simple_prio(lambda x: x.needs_concept_generation(), p),
             lambda p: "Atratividade mede valor percebido e adoção conceitual."),
    ToolRule("G4_TEST01", lambda p: p.is_innovation() or p.has_patient_contact or p.user_type in ["patient_or_caregiver", "multiple_users"],
             lambda p: _prio(lambda x: x.is_radical() or x.is_class_high(), p),
             lambda p: "Teste de conceito avalia entendimento e aceitação, sem validar produto."),
    ToolRule("G4_PROTO01", lambda p: p.needs_concept_generation() and p.complexity_gte(ComplexityLevel.MEDIUM),
             lambda p: ToolPriority.RECOMMENDED,
             lambda p: "Protótipo de apoio melhora comunicação e teste de conceito."),
    ToolRule("G4_SCORE01", lambda p: p.needs_concept_generation() or p.is_innovation() or p.is_product_similar(),
             lambda p: ToolPriority.RECOMMENDED,
             lambda p: "Scorecard consolida seleção do conceito."),
    ToolRule("G4_UNC01", lambda p: len(p.concept_uncertainties) > 0 or p.complexity_gte(ComplexityLevel.MEDIUM),
             lambda p: ToolPriority.RECOMMENDED,
             lambda p: "Mapa de incertezas do conceito selecionado apoia transferência."),

    # Gate 5
    ToolRule("G5_MISSION01", lambda p: not p.is_fast_track_resale() or p.needs_internal_approval,
             lambda p: _simple_prio(lambda x: x.is_innovation() or x.needs_internal_approval, p),
             lambda p: "Missão do conceito consolida objetivo e fronteiras."),
    ToolRule("G5_REQ01", lambda p: not p.is_fast_track_resale() or p.has_patient_contact,
             lambda p: _simple_prio(lambda x: x.is_innovation() or x.has_patient_contact, p),
             lambda p: "Requisitos conceituais são de alto nível, sem especificação final."),
    ToolRule("G5_UNS01", lambda p: p.is_innovation() or p.has_patient_contact or p.problem_clarity < 2,
             lambda p: _prio(lambda x: x.is_innovation(), p),
             lambda p: "User Needs Statement formaliza necessidades para o projeto."),
    ToolRule("G5_CTQ01", lambda p: p.is_innovation() or p.complexity_gte(ComplexityLevel.MEDIUM) or p.has_patient_contact,
             lambda p: _prio(lambda x: x.is_radical() or x.is_class_high(), p),
             lambda p: "CTQ consolidado registra atributos críticos escolhidos."),
    ToolRule("G5_QFD01", lambda p: p.is_innovation() or p.is_class_high() or p.multi_stakeholder,
             lambda p: _prio(lambda x: x.is_radical() or x.multi_stakeholder, p),
             lambda p: "QFD consolidado registra relação necessidade × requisito conceitual."),
    ToolRule("G5_CLAIMS01", lambda p: p.is_innovation() or p.has_associated_drug or p.is_product_similar(),
             lambda p: _prio(lambda x: x.has_associated_drug or x.is_radical(), p),
             lambda p: "Claims pretendidos registram alegações desejadas, não finais."),
    ToolRule("G5_UNC01", lambda p: len(p.concept_uncertainties) > 0 or p.complexity_gte(ComplexityLevel.MEDIUM),
             lambda p: _prio(lambda x: x.complexity_gte(ComplexityLevel.HIGH), p),
             lambda p: "Mapa final de incertezas orienta o time de projeto."),
    ToolRule("G5_LRN01", lambda p: len(p.concept_uncertainties) > 0 or p.is_innovation(),
             lambda p: _prio(lambda x: x.is_radical() or x.is_class_high(), p),
             lambda p: "Plano de aprendizagem indica investigações futuras."),
    ToolRule("G5_PREM01", _always, lambda p: _simple_prio(lambda x: not x.is_simple_project(), p),
             lambda p: "Premissas e restrições dão rastreabilidade ao conceito."),
    ToolRule("G5_RECOM01", lambda p: not p.is_fast_track_resale() or len(p.concept_uncertainties) > 0,
             lambda p: _simple_prio(lambda x: x.complexity_gte(ComplexityLevel.MEDIUM), p),
             lambda p: "Recomendações orientam a próxima fase sem executar projeto."),
    ToolRule("G5_ONEPAGE01", _always, lambda p: ToolPriority.MANDATORY,
             lambda p: "One-Page Concept é entrega mínima para qualquer rota."),
    ToolRule("G5_REPORT01", lambda p: not p.is_fast_track_resale(),
             lambda p: _simple_prio(lambda x: x.needs_internal_approval or x.is_innovation(), p),
             lambda p: "Relatório final consolida decisões dos gates."),
    ToolRule("G5_TERM01", lambda p: p.needs_internal_approval or p.is_innovation() or p.is_class_high(),
             lambda p: _prio(lambda x: x.needs_internal_approval or x.is_class_high(), p),
             lambda p: "Termo formaliza aprovação quando há governança ou complexidade elevada."),
    ToolRule("G5_TRANSFER01", _always, lambda p: ToolPriority.MANDATORY,
             lambda p: "Pacote de transferência conceitual entrega decisões e pendências ao projeto."),
]


# =============================================================================
# QUESTIONÁRIO ADAPTATIVO
# =============================================================================

def _is_simple_strategy(p: ProjectProfile) -> bool:
    return set(p.development_strategy) <= {"oem_pure", "white_label", "doc_adaptation"}


def build_questionnaire() -> dict[str, Question]:
    def h_origin(v: str, p: ProjectProfile) -> list[str]:
        p.project_origin = {
            "A": "internal",
            "B": "client",
            "C": "market",
            "D": "clinical_field",
        }[v]
        return ["Q02"]

    def h_strategy(vs: list[str], p: ProjectProfile) -> list[str]:
        strategy_map = {
            "A": "oem_pure",
            "B": "white_label",
            "C": "doc_adaptation",
            "D": "tech_adaptation",
            "E": "material_change",
            "F": "supplier_change",
            "G": "nationalization",
            "H": "inhouse_production",
            "I": "new_kit",
            "J": "new_accessory",
            "K": "similar_competitor",
            "L": "incremental_innovation",
            "M": "radical_innovation",
            "N": "platform",
        }
        p.development_strategy = [strategy_map[v] for v in vs if v in strategy_map]
        return ["Q03"]

    def h_responsibility(vs: list[str], p: ProjectProfile) -> list[str]:
        rmap = {
            "A": "brand_owner",
            "B": "regulatory_holder",
            "C": "technical_responsible",
            "D": "manufacturer",
            "E": "importer",
            "F": "distributor",
        }
        p.company_responsibility = [rmap[v] for v in vs if v in rmap]
        return ["Q_CLASS"]

    def h_class(v: str, p: ProjectProfile) -> list[str]:
        cmap = {
            "A": RegulatoryClass.CLASS_I,
            "B": RegulatoryClass.CLASS_II,
            "C": RegulatoryClass.CLASS_III,
            "D": RegulatoryClass.CLASS_IV,
            "E": RegulatoryClass.UNKNOWN,
        }
        p.regulatory_class = cmap[v]
        p.regulatory_class_known = v != "E"
        p.regulatory_uncertainty = "low" if v in ["A", "B"] else ("medium" if v == "C" else "high")
        if p.regulatory_class == RegulatoryClass.CLASS_IV:
            p.add_uncertainty("regulatory_high_class")
        return ["Q_USER1"]

    def h_user1(v: str, p: ProjectProfile) -> list[str]:
        mapping = {
            "A": "physician",
            "B": "nurse_or_technician",
            "C": "patient_or_caregiver",
            "D": "internal_production",
            "E": "institutional_buyer",
            "F": "multiple_users",
        }
        p.user_type = mapping[v]
        if v == "F":
            p.multi_stakeholder = True
        return ["Q04"]

    def h_patient_contact(v: str, p: ProjectProfile) -> list[str]:
        p.invasiveness_level = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}[v]
        p.has_patient_contact = v != "A"
        if p.invasiveness_level >= 2:
            p.add_uncertainty("patient_contact")
        return ["Q05"]

    def h_sterility(v: str, p: ProjectProfile) -> list[str]:
        p.sterility_required = v == "A"
        p.sterility_unknown = v == "C"
        if v == "C":
            p.add_uncertainty("sterility")
            p.packaging_change_required = True
        else:
            p.remove_uncertainty("sterility")

        next_qs: list[str] = []
        if p.is_oem():
            next_qs += ["Q_OEM1", "Q_OEM2", "Q_OEM3"]
        if p.is_supplier_change():
            next_qs += ["Q_SUP1"]
        if p.is_adaptation():
            next_qs += ["Q_ADP1", "Q_ADP2"]
        if p.is_kit_or_accessory():
            next_qs += ["Q_KIT1"]
        if p.is_product_similar():
            next_qs += ["Q_SIM1"]
        if p.is_inhouse():
            next_qs += ["Q_INT1"]
        if p.is_innovation():
            next_qs += ["Q_INN1", "Q_INN2"]

        simple_now = _is_simple_strategy(p) and p.regulatory_class in [RegulatoryClass.CLASS_I, RegulatoryClass.CLASS_II]
        if not simple_now:
            next_qs += ["Q_CROSS1", "Q_CROSS2", "Q_CROSS3", "Q_CROSS4", "Q_CROSS5", "Q_CROSS6", "Q_CROSS7", "Q_CROSS8"]
        elif p.has_patient_contact or p.sterility_required or not p.regulatory_class_known:
            next_qs += ["Q_CROSS1", "Q_CROSS6"]

        if p.is_radical() or p.is_platform() or p.is_class_iv():
            next_qs += ["Q_ADV1", "Q_ADV2", "Q_ADV3", "Q_ADV4", "Q_ADV5", "Q_ADV6"]

        next_qs += ["Q_FINAL"]
        return next_qs

    def h_oem1(v: str, p: ProjectProfile) -> list[str]:
        p.supplier_dependency = {"A": "external_defined", "B": "external_undefined", "C": "external_undefined"}[v]
        p.has_multiple_suppliers = v == "C"
        if v in ["B", "C"]:
            p.add_uncertainty("supplier")
        return []

    def h_oem2(vs: list[str], p: ProjectProfile) -> list[str]:
        if "D" in vs:
            p.labeling_change_required = False
            p.ifu_change_required = False
            p.packaging_change_required = False
            return []
        if "A" in vs:
            p.labeling_change_required = True
        if "B" in vs:
            p.ifu_change_required = True
        if "C" in vs:
            p.packaging_change_required = True
        if any(v in vs for v in ["A", "B", "C"]):
            p.add_uncertainty("customization")
        return []

    def h_oem3(v: str, p: ProjectProfile) -> list[str]:
        p.cost_is_critical = v in ["A", "B"]
        if p.cost_is_critical:
            p.add_uncertainty("cost")
        return []

    def h_sup1(v: str, p: ProjectProfile) -> list[str]:
        p.supplier_dependency = "external_defined" if v == "A" else "external_undefined"
        p.has_multiple_suppliers = v == "C"
        if v != "A":
            p.add_uncertainty("supplier")
        return []

    def h_adp1(vs: list[str], p: ProjectProfile) -> list[str]:
        if "C" in vs and "material_change" not in p.development_strategy:
            p.development_strategy.append("material_change")
            p.add_uncertainty("material")
        if "D" in vs:
            p.packaging_change_required = True
            p.add_uncertainty("packaging")
        if "E" in vs:
            p.labeling_change_required = True
            p.ifu_change_required = True
            p.add_uncertainty("labeling_ifu")
        if "F" in vs and "process_change" not in p.development_strategy:
            p.development_strategy.append("process_change")
            p.add_uncertainty("manufacturing")
        if "B" in vs:
            p.add_uncertainty("intended_use")
        return []

    def h_adp2(v: str, p: ProjectProfile) -> list[str]:
        p.has_existing_reference = v in ["A", "B"]
        p.reference_is_competitor = v == "A"
        p.reference_is_own = v == "B"
        return []

    def h_kit1(vs: list[str], p: ProjectProfile) -> list[str]:
        if "B" in vs:
            p.sterility_required = True
            p.sterility_unknown = False
            p.remove_uncertainty("sterility")
        if "C" in vs:
            p.packaging_change_required = True
            p.add_uncertainty("packaging")
        if "D" in vs:
            p.ifu_change_required = True
            p.add_uncertainty("labeling_ifu")
        if "E" in vs:
            p.has_existing_reference = True
        return []

    def h_sim1(v: str, p: ProjectProfile) -> list[str]:
        p.has_existing_reference = True
        p.reference_is_competitor = True
        p.has_market_benchmark = v == "A"
        if v != "A":
            p.add_uncertainty("benchmark")
        return []

    def h_int1(v: str, p: ProjectProfile) -> list[str]:
        p.manufacturing_strategy = {"A": "assembly", "B": "component", "C": "full", "D": "unknown"}[v]
        if v in ["B", "C", "D"]:
            p.add_uncertainty("manufacturing")
        if v == "D":
            p.likely_manufacturing_complexity = "unknown"
        if v == "C":
            p.likely_manufacturing_complexity = "high"
        return []

    def h_inn1(v: str, p: ProjectProfile) -> list[str]:
        p.tech_maturity = {"A": 3, "B": 2, "C": 1, "D": 0}[v]
        if v in ["C", "D"]:
            p.add_uncertainty("technology")
        return []

    def h_inn2(vs: list[str], p: ProjectProfile) -> list[str]:
        imap = {
            "A": "clinical_evidence", "B": "ip_space", "C": "technology", "D": "supplier",
            "E": "regulatory", "F": "cost", "G": "manufacturing", "H": "user_acceptance"
        }
        for v in vs:
            if v in imap:
                p.add_uncertainty(imap[v])
        if "B" in vs:
            p.ip_uncertainty = True
        return []

    def h_cross1(v: str, p: ProjectProfile) -> list[str]:
        p.problem_clarity = {"A": 2, "B": 1, "C": 0}[v]
        if v != "A":
            p.add_uncertainty("problem_definition")
        return []

    def h_cross2(v: str, p: ProjectProfile) -> list[str]:
        p.need_evidence_level = {"A": 2, "B": 1, "C": 0}[v]
        if v != "A":
            p.add_uncertainty("need_evidence")
        return []

    def h_cross3(v: str, p: ProjectProfile) -> list[str]:
        p.multi_stakeholder = v == "A" or p.user_type == "multiple_users"
        return []

    def h_cross4(v: str, p: ProjectProfile) -> list[str]:
        p.has_digital_component = v == "A"
        if v == "A":
            p.add_uncertainty("digital_component")
        return []

    def h_cross5(v: str, p: ProjectProfile) -> list[str]:
        p.has_field_observation = v == "A"
        if v == "B" and (p.is_innovation() or p.critical_use):
            p.add_uncertainty("field_observation")
        return []

    def h_cross6(v: str, p: ProjectProfile) -> list[str]:
        p.has_associated_drug = v in ["A", "B"]
        if v in ["A", "B"]:
            p.add_uncertainty("clinical_evidence")
            p.add_uncertainty("regulatory")
        elif v == "D":
            p.add_uncertainty("regulatory")
        return []

    def h_cross7(v: str, p: ProjectProfile) -> list[str]:
        p.critical_use = v == "A"
        if v == "A":
            p.add_uncertainty("critical_use")
        return []

    def h_cross8(v: str, p: ProjectProfile) -> list[str]:
        p.needs_internal_approval = v == "A"
        return []

    def h_adv1(v: str, p: ProjectProfile) -> list[str]:
        p.claims_uncertain = v in ["B", "C"]
        if p.claims_uncertain:
            p.add_uncertainty("claims")
        return []

    def h_adv2(v: str, p: ProjectProfile) -> list[str]:
        p.ip_uncertainty = v in ["B", "C"]
        if p.ip_uncertainty:
            p.add_uncertainty("ip_space")
        return []

    def h_adv3(v: str, p: ProjectProfile) -> list[str]:
        p.likely_manufacturing_complexity = {"A": "low", "B": "medium", "C": "high", "D": "unknown"}[v]
        if v in ["C", "D"]:
            p.add_uncertainty("manufacturing")
        return []

    def h_adv4(v: str, p: ProjectProfile) -> list[str]:
        p.expected_volume = {"A": "low", "B": "medium", "C": "high", "D": "unknown"}[v]
        if v == "D":
            p.add_uncertainty("market_volume")
        return []

    def h_adv5(v: str, p: ProjectProfile) -> list[str]:
        if v in ["B", "C"]:
            p.add_uncertainty("concept_test")
        return []

    def h_adv6(v: str, p: ProjectProfile) -> list[str]:
        if v in ["B", "C"]:
            p.add_uncertainty("principle_proof")
        return []

    def h_final(v: str, p: ProjectProfile) -> list[str]:
        p.timeline = {"A": "short", "B": "medium", "C": "long"}[v]
        return []

    return {
        "Q01": Question("Q01", "Qual é a origem deste projeto?", {
            "A": "Demanda interna da empresa",
            "B": "Demanda de cliente ou parceiro externo",
            "C": "Oportunidade identificada no mercado",
            "D": "Necessidade clínica observada em campo",
        }, h_origin),

        "Q02": Question("Q02", "Qual é a estratégia de desenvolvimento deste produto?", {
            "A": "Produto pronto para comprar e revender",
            "B": "White label / marca própria sobre produto externo",
            "C": "Adaptação documental: marca, IFU, rótulo ou embalagem",
            "D": "Adaptação técnica: design, ergonomia, indicação ou uso",
            "E": "Alteração de material do produto",
            "F": "Substituição de fornecedor de produto atual",
            "G": "Nacionalização de componente ou produto importado",
            "H": "Internalização produtiva futura",
            "I": "Novo kit médico",
            "J": "Novo acessório para produto existente",
            "K": "Produto similar a concorrente / me-too",
            "L": "Inovação incremental",
            "M": "Inovação radical",
            "N": "Plataforma tecnológica ou família de produtos",
        }, h_strategy, multiple=True, help_text="Selecione todas as estratégias aplicáveis."),

        "Q03": Question("Q03", "Qual responsabilidade a empresa assumirá com este produto?", {
            "A": "Titular da marca",
            "B": "Titular do registro ou notificação",
            "C": "Responsável técnico pelo produto",
            "D": "Fabricante",
            "E": "Importador",
            "F": "Distribuidor",
        }, h_responsibility, multiple=True),

        "Q_CLASS": Question("Q_CLASS", "Qual é a classe regulatória provável ou conhecida do produto?", {
            "A": "Classe I",
            "B": "Classe II",
            "C": "Classe III",
            "D": "Classe IV",
            "E": "Não sei ainda",
        }, h_class),

        "Q_USER1": Question("Q_USER1", "Quem será o usuário principal do produto?", {
            "A": "Médico / cirurgião",
            "B": "Enfermeiro / técnico de saúde",
            "C": "Paciente / cuidador",
            "D": "Equipe interna de produção ou processamento",
            "E": "Hospital / clínica / comprador institucional",
            "F": "Múltiplos usuários principais",
        }, h_user1),

        "Q04": Question("Q04", "O produto terá contato com o paciente?", {
            "A": "Não terá contato com paciente",
            "B": "Contato externo com pele íntegra",
            "C": "Contato com mucosa ou orifício natural",
            "D": "Invasivo temporário",
            "E": "Implantável ou longa permanência",
        }, h_patient_contact),

        "Q05": Question("Q05", "O produto precisará ser estéril?", {
            "A": "Sim, estéril confirmado",
            "B": "Não",
            "C": "Não sei ainda",
        }, h_sterility),

        "Q_OEM1": Question("Q_OEM1", "[OEM] Qual é a situação atual do fornecedor externo?", {
            "A": "Fornecedor definido",
            "B": "Fornecedor ainda não definido",
            "C": "Múltiplos fornecedores em avaliação",
        }, h_oem1),

        "Q_OEM2": Question("Q_OEM2", "[OEM] Haverá customização do produto externo?", {
            "A": "Rótulo, idioma ou marca",
            "B": "IFU / instruções de uso",
            "C": "Embalagem ou apresentação",
            "D": "Nenhuma customização prevista",
        }, h_oem2, multiple=True, exclusive_options={"D"}),

        "Q_OEM3": Question("Q_OEM3", "[OEM] O custo unitário é fator crítico para decisão?", {
            "A": "Sim, custo é decisivo",
            "B": "Sim, mas não é o único critério",
            "C": "Não, outros fatores predominam",
        }, h_oem3),

        "Q_SUP1": Question("Q_SUP1", "[Fornecedor] Como está a situação do fornecedor alternativo?", {
            "A": "Alternativo identificado",
            "B": "Alternativo ainda em prospecção",
            "C": "Múltiplos alternativos em avaliação",
        }, h_sup1),

        "Q_ADP1": Question("Q_ADP1", "[Adaptação] O que poderá ser modificado?", {
            "A": "Ergonomia, design ou interface",
            "B": "Indicação clínica ou uso pretendido",
            "C": "Material ou composição",
            "D": "Embalagem ou apresentação",
            "E": "Rotulagem ou IFU",
            "F": "Processo produtivo futuro",
        }, h_adp1, multiple=True),

        "Q_ADP2": Question("Q_ADP2", "[Adaptação] Existe produto de referência?", {
            "A": "Sim, produto concorrente",
            "B": "Sim, produto próprio atual",
            "C": "Não há referência direta",
        }, h_adp2),

        "Q_KIT1": Question("Q_KIT1", "[Kit/Acessório] Quais características se aplicam?", {
            "A": "Agrupa produtos de fornecedores diferentes",
            "B": "Pelo menos um componente é estéril",
            "C": "Pode exigir embalagem específica",
            "D": "Pode exigir IFU específica",
            "E": "Acessório deve ser compatível com produto já registrado",
        }, h_kit1, multiple=True),

        "Q_SIM1": Question("Q_SIM1", "[Produto similar] O produto de referência está disponível?", {
            "A": "Sim, temos acesso físico ao produto",
            "B": "Acesso parcial por especificações ou literatura",
            "C": "Não, apenas informações públicas",
        }, h_sim1),

        "Q_INT1": Question("Q_INT1", "[Internalização] Qual escopo produtivo é previsto?", {
            "A": "Apenas montagem final",
            "B": "Fabricação de componentes principais",
            "C": "Produção integral futura",
            "D": "Ainda não definido",
        }, h_int1),

        "Q_INN1": Question("Q_INN1", "[Inovação] Qual é a maturidade da tecnologia central?", {
            "A": "Consolidada e dominada internamente",
            "B": "Existente no mercado, nova para a empresa",
            "C": "Emergente, ainda em desenvolvimento",
            "D": "Inédita ou sem precedente claro",
        }, h_inn1),

        "Q_INN2": Question("Q_INN2", "[Inovação] Quais são as principais incertezas abertas?", {
            "A": "Evidência clínica",
            "B": "Espaço de propriedade intelectual",
            "C": "Viabilidade técnica",
            "D": "Fornecedor de componentes-chave",
            "E": "Caminho regulatório",
            "F": "Custo",
            "G": "Manufatura futura",
            "H": "Aceitação do usuário",
        }, h_inn2, multiple=True),

        "Q_CROSS1": Question("Q_CROSS1", "Qual é a clareza do problema clínico ou operacional?", {
            "A": "Claro e bem documentado",
            "B": "Parcialmente definido",
            "C": "Vago, ainda em entendimento",
        }, h_cross1),

        "Q_CROSS2": Question("Q_CROSS2", "A necessidade já possui evidência ou validação inicial?", {
            "A": "Sim, evidência clara ou VOC suficiente",
            "B": "Parcialmente",
            "C": "Não, ainda é hipótese",
        }, h_cross2),

        "Q_CROSS3": Question("Q_CROSS3", "O projeto envolve múltiplos stakeholders?", {
            "A": "Sim",
            "B": "Não",
        }, h_cross3),

        "Q_CROSS4": Question("Q_CROSS4", "O produto terá componente digital, software, app, IA ou IoT?", {
            "A": "Sim",
            "B": "Não",
        }, h_cross4),

        "Q_CROSS5": Question("Q_CROSS5", "Já houve observação em campo ou visita a usuários reais?", {
            "A": "Sim",
            "B": "Não",
        }, h_cross5),

        "Q_CROSS6": Question("Q_CROSS6", "Haverá interação com medicamento, fluido, substância química ou solução clínica?", {
            "A": "Sim, medicamento ou substância ativa",
            "B": "Sim, fluido ou solução clínica",
            "C": "Não",
            "D": "Não sei ainda",
        }, h_cross6),

        "Q_CROSS7": Question("Q_CROSS7", "O uso do produto pode envolver tarefa crítica ou erro de uso relevante?", {
            "A": "Sim",
            "B": "Não",
            "C": "Não sei ainda",
        }, h_cross7),

        "Q_CROSS8": Question("Q_CROSS8", "O conceito precisará de aprovação formal interna antes de ir ao projeto?", {
            "A": "Sim",
            "B": "Não",
        }, h_cross8),

        "Q_ADV1": Question("Q_ADV1", "[Avançado] Os claims pretendidos já estão claros?", {
            "A": "Sim, claros",
            "B": "Parcialmente",
            "C": "Não",
        }, h_adv1),

        "Q_ADV2": Question("Q_ADV2", "[Avançado] Já existe noção de liberdade de operação / FTO?", {
            "A": "Sim, preliminarmente verificada",
            "B": "Parcialmente",
            "C": "Não",
        }, h_adv2),

        "Q_ADV3": Question("Q_ADV3", "[Avançado] A rota produtiva provável parece complexa?", {
            "A": "Baixa complexidade",
            "B": "Média complexidade",
            "C": "Alta complexidade",
            "D": "Não sei ainda",
        }, h_adv3),

        "Q_ADV4": Question("Q_ADV4", "[Avançado] Qual volume esperado de uso ou venda?", {
            "A": "Baixo",
            "B": "Médio",
            "C": "Alto",
            "D": "Não sei ainda",
        }, h_adv4),

        "Q_ADV5": Question("Q_ADV5", "[Avançado] Será necessário teste de conceito com usuário/KOL?", {
            "A": "Sim, necessário",
            "B": "Talvez",
            "C": "Não sei",
        }, h_adv5),

        "Q_ADV6": Question("Q_ADV6", "[Avançado] Será necessário prova de princípio antes do projeto?", {
            "A": "Sim, necessário",
            "B": "Talvez",
            "C": "Não sei",
        }, h_adv6),

        "Q_FINAL": Question("Q_FINAL", "Horizonte esperado para aprovação do conceito:", {
            "A": "Curto prazo — até 3 meses",
            "B": "Médio prazo — 3 a 6 meses",
            "C": "Longo prazo — mais de 6 meses",
        }, h_final),
    }


# =============================================================================
# ENGINE PRINCIPAL
# =============================================================================

class MedConceptEngine:
    def __init__(self):
        self.profile = ProjectProfile()
        self.answered: set[str] = set()
        self.queue: list[str] = ["Q01"]
        self.questions = build_questionnaire()
        self.finished = False

    def get_current_question(self) -> Question | None:
        while self.queue:
            qid = self.queue[0]
            if qid in self.answered or qid not in self.questions:
                self.queue.pop(0)
                continue
            return self.questions[qid]
        self.finished = True
        self.profile.compute_complexity()
        return None

    def answer_current_question(self, value: str | list[str]) -> None:
        q = self.get_current_question()
        if q is None:
            self.finished = True
            self.profile.compute_complexity()
            return

        qid = q.id
        if q.multiple:
            selected = value if isinstance(value, list) else [str(value)]
            selected = [str(v) for v in selected]
            if not selected:
                raise ValueError("Selecione pelo menos uma opção.")
            for v in selected:
                if v not in q.options:
                    raise ValueError("Resposta inválida.")
            overlap = set(selected) & q.exclusive_options
            if overlap and len(selected) > 1:
                labels = ", ".join(q.options[o] for o in overlap)
                raise ValueError(f"A opção '{labels}' não pode ser combinada com outras opções.")
            labels = [q.options[v] for v in selected]
            self.profile.raw_answers.append({"q": qid, "value": selected, "label": labels})
            next_ids = q.handler(selected, self.profile)
        else:
            if not isinstance(value, str) or value not in q.options:
                raise ValueError("Resposta inválida.")
            self.profile.raw_answers.append({"q": qid, "value": value, "label": q.options[value]})
            next_ids = q.handler(value, self.profile)

        self.answered.add(qid)
        if self.queue and self.queue[0] == qid:
            self.queue.pop(0)

        for nid in next_ids:
            if nid not in self.answered and nid not in self.queue:
                self.queue.append(nid)

        if not self.queue:
            self.finished = True
            self.profile.compute_complexity()

    def progress(self) -> tuple[int, int, float]:
        total = len(self.answered) + len([q for q in self.queue if q not in self.answered])
        answered = len(self.answered)
        ratio = 1.0 if total == 0 else answered / total
        return answered, total, ratio

    # ------------------------------------------------------------------
    # Rotas e limites de pacote
    # ------------------------------------------------------------------
    def project_route(self) -> str:
        p = self.profile
        p.compute_complexity()
        if p.is_fast_track_resale():
            return "Revenda simples / Classe I"
        if p.is_oem() and p.regulatory_class in [RegulatoryClass.CLASS_I, RegulatoryClass.CLASS_II]:
            return "OEM / White label"
        if p.is_supplier_change():
            return "Substituição de fornecedor"
        if p.is_product_similar():
            return "Produto similar / me-too"
        if p.is_kit_or_accessory():
            return "Novo kit ou acessório"
        if p.is_inhouse():
            return "Internalização / nacionalização"
        if "incremental_innovation" in p.development_strategy:
            return "Inovação incremental"
        if p.is_radical() and p.is_class_iv():
            return "Inovação radical Classe IV"
        if p.is_radical() or p.is_platform() or p.complexity == ComplexityLevel.ULTRA:
            return "Inovação radical / plataforma"
        if p.is_adaptation():
            return "Adaptação de produto existente"
        return "Rota conceitual padrão"

    def recommendation_cap(self) -> int:
        p = self.profile
        p.compute_complexity()
        if p.is_fast_track_resale():
            return 10
        if p.is_oem() and p.regulatory_class in [RegulatoryClass.CLASS_I, RegulatoryClass.CLASS_II]:
            return 12
        if p.is_supplier_change():
            return 15
        if p.is_adaptation() and not p.needs_concept_generation():
            return 12
        if p.is_product_similar():
            return 16
        if p.is_kit_or_accessory():
            return 18
        if p.is_inhouse():
            return 20
        if "incremental_innovation" in p.development_strategy:
            return 24
        if p.is_radical() and p.is_class_iv():
            return 40
        if p.is_radical() or p.is_platform() or p.complexity == ComplexityLevel.ULTRA:
            return 35
        return 14

    def tool_gate(self, tool_id: str) -> int:
        if tool_id.startswith("G1_"):
            return 1
        if tool_id.startswith("G2_"):
            return 2
        if tool_id.startswith("G3_"):
            return 3
        if tool_id.startswith("G4_"):
            return 4
        if tool_id.startswith("G5_"):
            return 5
        return 0

    def tool_gate_label(self, tool_id: str) -> str:
        labels = {
            1: "Gate 1 — Oportunidade e Necessidade",
            2: "Gate 2 — Estratégia Conceitual e Requisitos de Alto Nível",
            3: "Gate 3 — Geração de Alternativas",
            4: "Gate 4 — Seleção e Teste do Conceito",
            5: "Gate 5 — Conceito Final Aprovado",
        }
        return labels.get(self.tool_gate(tool_id), "Sem Gate")

    def _priority_score(self, item: SelectedTool) -> int:
        base = {
            ToolPriority.MANDATORY: 100,
            ToolPriority.RECOMMENDED: 60,
            ToolPriority.OPTIONAL: 20,
        }[item.priority]
        if item.tool.category == ToolCategory.DECISION:
            base += 100
        if item.tool.id in {"G1_OPP01", "G2_STR01", "G5_ONEPAGE01", "G5_TRANSFER01"}:
            base += 90
        if item.tool.id.startswith("G2_") and self.profile.is_oem():
            base += 10
        if item.tool.id.startswith("G3_") and self.profile.needs_concept_generation():
            base += 10
        return base

    def _core_tool_ids(self) -> list[str]:
        p = self.profile
        ids = ["G1_GO01", "G2_GO01", "G3_GO01", "G4_GO01", "G5_GO01", "G1_OPP01", "G2_STR01", "G5_ONEPAGE01", "G5_TRANSFER01"]
        if p.is_fast_track_resale():
            ids += ["G2_OEM01"]
            if p.labeling_change_required or p.ifu_change_required or p.packaging_change_required or p.is_white_label():
                ids += ["G2_CUS01"]
            return ids
        if p.is_oem():
            ids += ["G1_BEN01", "G2_OEM01", "G2_SUP01"]
            if p.is_white_label() or p.labeling_change_required or p.ifu_change_required or p.packaging_change_required:
                ids += ["G2_CUS01"]
        if p.is_supplier_change():
            ids += ["G2_SUP01", "G2_SIM01"]
        if p.is_adaptation() or p.is_product_similar():
            ids += ["G2_SIM01", "G4_REF01", "G4_CRIT01"]
        if p.is_kit_or_accessory():
            ids += ["G2_KIT01", "G2_CUS01"]
        if p.is_inhouse():
            ids += ["G2_INT01", "G2_PROD01", "G2_ECO01"]
        if p.is_innovation():
            ids += ["G1_VOC01", "G2_NEED01", "G2_NEED02", "G2_QFD01", "G2_CTQ01", "G3_BRAIN01", "G4_CRIT01", "G4_NEEDCON01"]
        return ids

    def apply_rules_raw(self) -> list[SelectedTool]:
        p = self.profile
        p.compute_complexity()
        result: list[SelectedTool] = []
        seen: set[str] = set()
        for rule in RULES:
            if rule.tool_id in seen or rule.tool_id not in TOOL_LIBRARY:
                continue
            try:
                if rule.condition(p):
                    result.append(SelectedTool(TOOL_LIBRARY[rule.tool_id], rule.priority_fn(p), rule.reason_fn(p)))
                    seen.add(rule.tool_id)
            except Exception as exc:
                raise RuntimeError(f"Erro ao aplicar regra da ferramenta {rule.tool_id}: {exc}") from exc
        result.sort(key=lambda x: (-self._priority_score(x), self.tool_gate(x.tool.id), x.tool.id))
        return result

    def _ensure_tool(self, raw_by_id: dict[str, SelectedTool], tid: str, priority: ToolPriority, reason: str) -> SelectedTool | None:
        if tid in raw_by_id:
            item = raw_by_id[tid]
            if priority == ToolPriority.MANDATORY and item.priority != ToolPriority.MANDATORY:
                return SelectedTool(item.tool, priority, reason)
            return item
        if tid in TOOL_LIBRARY:
            return SelectedTool(TOOL_LIBRARY[tid], priority, reason)
        return None

    def _curate_tools(self, raw: list[SelectedTool]) -> list[SelectedTool]:
        cap = self.recommendation_cap()
        raw_by_id = {item.tool.id: item for item in raw}
        selected: list[SelectedTool] = []
        selected_ids: set[str] = set()

        for tid in self._core_tool_ids():
            item = self._ensure_tool(raw_by_id, tid, ToolPriority.MANDATORY, "Ferramenta núcleo do pacote mínimo para esta rota.")
            if item and tid not in selected_ids:
                selected.append(item)
                selected_ids.add(tid)

        candidates = [x for x in raw if x.tool.id not in selected_ids and x.priority != ToolPriority.OPTIONAL]
        candidates.sort(key=lambda x: (-self._priority_score(x), self.tool_gate(x.tool.id), x.tool.id))
        for item in candidates:
            if len(selected) >= cap:
                break
            selected.append(item)
            selected_ids.add(item.tool.id)

        # Nunca ultrapassar muito o limite, exceto se core já passou.
        order = {ToolPriority.MANDATORY: 0, ToolPriority.RECOMMENDED: 1, ToolPriority.OPTIONAL: 2}
        selected.sort(key=lambda x: (self.tool_gate(x.tool.id), order[x.priority], x.tool.id))
        return selected

    def apply_rules(self) -> list[SelectedTool]:
        return self._curate_tools(self.apply_rules_raw())

    def selected_as_groups(self, selected: list[SelectedTool]) -> dict[ToolPriority, list[SelectedTool]]:
        grouped = {ToolPriority.MANDATORY: [], ToolPriority.RECOMMENDED: [], ToolPriority.OPTIONAL: []}
        for item in selected:
            grouped[item.priority].append(item)
        return grouped

    # ------------------------------------------------------------------
    # Matrizes Go/No-Go
    # ------------------------------------------------------------------
    def gate_matrix(self, gate: int) -> dict[str, Any]:
        p = self.profile
        p.compute_complexity()

        def mark(condition: bool, partial: bool = False) -> str:
            if condition:
                return "Sim"
            if partial:
                return "Parcial"
            return "Não"

        if gate == 1:
            criteria = [
                ("Oportunidade descrita", True, "A origem e hipótese foram registradas."),
                ("Necessidade plausível", p.problem_clarity >= 1 or p.is_fast_track_resale(), "Problema claro ou produto de mercado já definido."),
                ("Usuário/cliente identificado", bool(p.user_type), "Perfil principal registrado."),
                ("Valor percebido inicial", True, "Será consolidado pela proposta de valor."),
                ("Sem incerteza impeditiva inicial", not (p.is_class_iv() and p.problem_clarity == 0), "Incertezas não bloqueiam a continuidade."),
            ]
        elif gate == 2:
            criteria = [
                ("Rota de desenvolvimento classificada", bool(p.development_strategy), "Estratégia informada no questionário."),
                ("Uso pretendido preliminar possível", bool(p.user_type), "Usuário e contato foram triados."),
                ("Regulatório triado", p.regulatory_class_known or p.regulatory_uncertainty != "", "Classe conhecida ou incerteza registrada."),
                ("Alertas principais identificados", True, "Triagens registram alertas sem limitar o conceito."),
                ("Próximo aprendizado definido", len(p.concept_uncertainties) > 0 or p.is_simple_project(), "Incertezas ou rota simples identificadas."),
            ]
        elif gate == 3:
            criteria = [
                ("Geração de alternativas aplicável", p.needs_concept_generation(), "Se produto pronto, Gate pode ser não aplicável."),
                ("Alternativas suficientes para comparar", p.needs_concept_generation(), "A definir pela equipe durante aplicação."),
                ("Soluções não limitadas prematuramente", True, "Apenas triagens conceituais são usadas."),
                ("Busca interna/externa considerada", p.needs_concept_generation() or p.is_reference_based(), "Referências apoiam alternativas."),
            ]
        elif gate == 4:
            criteria = [
                ("Critérios de seleção definidos", p.needs_concept_generation() or p.is_reference_based(), "Critérios orientam escolha."),
                ("Conceito de referência definido", p.has_existing_reference or p.is_oem() or p.is_reference_based(), "Referência pode ser produto atual, mercado ou solução padrão."),
                ("Aderência à necessidade avaliada", p.needs_concept_generation() or p.is_oem(), "Matriz necessidade × conceito ou atratividade apoia decisão."),
                ("Incertezas do conceito registradas", True, "Mapa de incertezas acompanha seleção."),
            ]
        else:
            criteria = [
                ("Conceito descrito", True, "One-Page Concept e relatório final consolidam."),
                ("Premissas e incertezas registradas", True, "Pacote conceitual deve conter pendências."),
                ("Recomendações para projeto claras", True, "Transferência conceitual orienta próxima fase."),
                ("Sem impedimento conceitual conhecido", not (p.is_class_iv() and p.problem_clarity == 0), "Se houver impedimento, decisão deve ser revisar/pausar."),
            ]

        rows = []
        no_count = 0
        partial_count = 0
        for name, ok, obs in criteria:
            value = mark(ok, partial=not ok and (p.is_fast_track_resale() or len(p.concept_uncertainties) > 0))
            if value == "Não":
                no_count += 1
            if value == "Parcial":
                partial_count += 1
            rows.append({"Critério": name, "Resultado": value, "Observação": obs})

        if no_count >= 2:
            decision = "No-Go"
        elif no_count == 1 or partial_count >= 2:
            decision = "Revisar"
        elif partial_count == 1:
            decision = "Pausar" if len(p.concept_uncertainties) >= 4 else "Go"
        else:
            decision = "Go"

        if gate in [3, 4] and p.is_fast_track_resale():
            decision = "Go simplificado"
            for row in rows:
                row["Observação"] += " Aplicável em formato simplificado para produto pronto."

        return {"gate": gate, "label": self.tool_gate_label(f"G{gate}_"), "rows": rows, "decision": decision}

    # ------------------------------------------------------------------
    # Relatórios e exportação
    # ------------------------------------------------------------------
    def _tools_by_gate(self, selected: list[SelectedTool]) -> dict[int, list[SelectedTool]]:
        data: dict[int, list[SelectedTool]] = {1: [], 2: [], 3: [], 4: [], 5: []}
        for item in selected:
            data.setdefault(self.tool_gate(item.tool.id), []).append(item)
        return data

    def _gate_intro(self, gate: int) -> str:
        intros = {
            1: "Avaliar se a oportunidade e a necessidade são reais, relevantes e compreendidas.",
            2: "Definir a estratégia conceitual e os requisitos de alto nível sem entrar em projeto detalhado.",
            3: "Gerar alternativas conceituais com liberdade criativa e sem congelar solução.",
            4: "Comparar alternativas, testar entendimento do conceito e selecionar a solução mais promissora.",
            5: "Consolidar o conceito final aprovado e preparar a transferência conceitual ao projeto.",
        }
        return intros[gate]

    def _gate_conclusion(self, gate: int, decision: str) -> str:
        if decision.startswith("Go"):
            return f"Com base na Matriz Go/No-Go do Gate {gate}, recomenda-se avançar conforme a rota definida."
        if decision == "Revisar":
            return f"Com base na Matriz Go/No-Go do Gate {gate}, recomenda-se revisar pontos pendentes antes de avançar."
        if decision == "Pausar":
            return f"Com base na Matriz Go/No-Go do Gate {gate}, recomenda-se pausar até obter informações críticas."
        return f"Com base na Matriz Go/No-Go do Gate {gate}, recomenda-se não avançar neste momento."

    def generate_report(self, selected: list[SelectedTool] | None = None) -> str:
        if selected is None:
            selected = self.apply_rules()
        p = self.profile
        p.compute_complexity()
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        by_gate = self._tools_by_gate(selected)

        lines: list[str] = []
        lines.append("=" * 100)
        lines.append("SISTEMA PARA GERAÇÃO DE CONCEITOS DE DISPOSITIVOS MÉDICOS — RELATÓRIO")
        lines.append("=" * 100)
        lines.append(f"Gerado em: {now}")
        lines.append(f"Rota identificada: {self.project_route()}")
        lines.append(f"Complexidade: {p.complexity.name} ({p.complexity_score} pontos)")
        lines.append(f"Limite do pacote principal: até {self.recommendation_cap()} ferramentas")
        lines.append("")
        lines.append("PERFIL RESUMIDO")
        lines.append("-" * 100)
        lines.append(f"Estratégias: {', '.join(p.development_strategy) or '—'}")
        lines.append(f"Responsabilidades: {', '.join(p.company_responsibility) or '—'}")
        lines.append(f"Classe regulatória: {p.regulatory_class.name}")
        lines.append(f"Contato com paciente: {'Sim' if p.has_patient_contact else 'Não'}")
        lines.append(f"Esterilidade: {'Sim' if p.sterility_required else ('Indefinida' if p.sterility_unknown else 'Não')}")
        lines.append(f"Incertezas: {', '.join(p.concept_uncertainties) or 'nenhuma registrada'}")
        lines.append("")

        for gate in range(1, 6):
            matrix = self.gate_matrix(gate)
            lines.append("=" * 100)
            lines.append(self.tool_gate_label(f"G{gate}_"))
            lines.append("=" * 100)
            lines.append("1. INTRODUÇÃO")
            lines.append(self._gate_intro(gate))
            lines.append("")
            lines.append("2. METODOLOGIA")
            tools = by_gate.get(gate, [])
            if tools:
                for item in tools:
                    lines.append(f"- {item.tool.name} ({item.priority.value}): {item.tool.description}")
                    if item.tool.subtools:
                        lines.append(f"  Subferramentas: {', '.join(item.tool.subtools)}")
            else:
                lines.append("- Nenhuma ferramenta principal selecionada para este Gate no pacote principal.")
            lines.append("")
            lines.append("3. RESULTADOS")
            lines.append("Síntese: as ferramentas selecionadas registram achados, alertas e incertezas sem executar projeto detalhado.")
            lines.append(f"Matriz Go/No-Go — Gate {gate}")
            for row in matrix["rows"]:
                lines.append(f"- {row['Critério']}: {row['Resultado']} | {row['Observação']}")
            lines.append(f"Resultado da matriz: {matrix['decision']}")
            lines.append("")
            lines.append("4. CONCLUSÃO")
            lines.append(self._gate_conclusion(gate, matrix["decision"]))
            lines.append("")

        return "\n".join(lines)

    def export_json(self, selected: list[SelectedTool] | None = None) -> dict[str, Any]:
        if selected is None:
            selected = self.apply_rules()
        p = self.profile
        p.compute_complexity()
        return {
            "generated_at": datetime.now().isoformat(),
            "engine_version": "v6-concept-gates-smart-questionnaire",
            "route": self.project_route(),
            "recommendation_cap": self.recommendation_cap(),
            "profile": {
                "development_strategy": p.development_strategy,
                "company_responsibility": p.company_responsibility,
                "project_origin": p.project_origin,
                "regulatory_class": p.regulatory_class.name,
                "has_patient_contact": p.has_patient_contact,
                "invasiveness_level": p.invasiveness_level,
                "sterility_required": p.sterility_required,
                "sterility_unknown": p.sterility_unknown,
                "has_digital_component": p.has_digital_component,
                "has_associated_drug": p.has_associated_drug,
                "critical_use": p.critical_use,
                "user_type": p.user_type,
                "multi_stakeholder": p.multi_stakeholder,
                "supplier_dependency": p.supplier_dependency,
                "concept_uncertainties": p.concept_uncertainties,
                "complexity": p.complexity.name,
                "complexity_score": p.complexity_score,
                "score_breakdown": p.score_breakdown,
            },
            "tools": [
                {
                    "id": item.tool.id,
                    "name": item.tool.name,
                    "gate": self.tool_gate(item.tool.id),
                    "gate_label": self.tool_gate_label(item.tool.id),
                    "category": item.tool.category.value,
                    "priority": item.priority.value,
                    "description": item.tool.description,
                    "subtools": item.tool.subtools,
                    "reason": item.reason,
                }
                for item in selected
            ],
            "gate_matrices": [self.gate_matrix(g) for g in range(1, 6)],
            "answers": p.raw_answers,
        }

    def export_json_string(self, selected: list[SelectedTool] | None = None) -> str:
        return json.dumps(self.export_json(selected), ensure_ascii=False, indent=2)
