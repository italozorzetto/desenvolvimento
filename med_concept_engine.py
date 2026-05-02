
"""
MED CONCEPT ENGINE v4 — Aplicativo Streamlit
Sistema Adaptativo de Desenvolvimento de Produtos Médicos

Escopo:
    Ciclo de Idealização → Conceito Aprovado → Entrega ao Time de Projeto

Arquitetura:
    1. app.py                 → controla tela inicial e navegação
    2. questionario.py        → renderiza questionário adaptativo
    3. med_concept_engine.py  → motor de regras, perguntas, ferramentas e relatório
"""

from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Any


# =============================================================================
# ENUMS
# =============================================================================

class ToolPriority(Enum):
    MANDATORY = "✅ Obrigatória"
    RECOMMENDED = "🔵 Recomendada"
    OPTIONAL = "⚪ Opcional"


class ToolCategory(Enum):
    OEM_SUPPLIER = "OEM / Fornecedor"
    SUPPLIER_CHANGE = "Substituição / Qualificação de Fornecedor"
    ADAPTATION = "Adaptação de Produto Existente"
    KIT_ACCESSORY = "Novo Kit ou Acessório"
    INTERNALIZATION = "Internalização / Produção Própria"
    REGULATORY = "Regulatório e Segurança (Preliminar)"
    NEED_RESEARCH = "Pesquisa de Necessidade"
    IDEATION = "Ideação e Geração de Conceito"
    MARKET_TECH = "Mercado e Tecnologia"
    REQUIREMENTS = "Requisitos Conceituais"
    CONCEPT_APPROVAL = "Seleção e Aprovação do Conceito"
    DELIVERABLES = "Entregáveis para o Time de Projeto"


class ComplexityLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    ULTRA = 4


# =============================================================================
# PERFIL MULTICAMADAS DO PRODUTO
# =============================================================================

@dataclass
class ProjectProfile:
    # Origem e estratégia
    project_origin: str = ""
    development_strategy: list[str] = field(default_factory=list)

    # Responsabilidade da empresa
    company_responsibility: list[str] = field(default_factory=list)

    # Natureza do produto
    has_patient_contact: bool = False
    invasiveness_level: int = 0
    sterility_required: bool = False
    sterility_unknown: bool = False
    has_digital_component: bool = False
    has_associated_drug: bool = False
    product_form: str = ""

    # Fornecedor / fabricação
    supplier_dependency: str = ""
    manufacturing_strategy: str = ""
    has_multiple_suppliers: bool = False
    cost_is_critical: bool = False

    # Novidade e tecnologia
    tech_maturity: int = 3
    has_existing_reference: bool = False
    reference_is_competitor: bool = False
    reference_is_own: bool = False

    # Mercado e usuário
    user_type: str = ""
    multi_stakeholder: bool = False

    # Regulatório
    regulatory_uncertainty: str = ""
    has_regulatory_class: bool = False
    has_similar_registration: bool = False
    labeling_change_required: bool = False
    ifu_change_required: bool = False
    packaging_change_required: bool = False
    norm_identified: bool = False

    # Incertezas abertas
    concept_uncertainties: list[str] = field(default_factory=list)

    # Clareza / contexto
    problem_clarity: int = 0
    has_field_observation: bool = False
    needs_internal_approval: bool = False
    timeline: str = ""

    # Respostas brutas
    raw_answers: list[dict[str, Any]] = field(default_factory=list)

    # Score calculado
    complexity: ComplexityLevel = ComplexityLevel.LOW
    complexity_score: int = 0
    score_breakdown: dict[str, int] = field(default_factory=dict)

    def add_uncertainty(self, value: str) -> None:
        if value not in self.concept_uncertainties:
            self.concept_uncertainties.append(value)

    def remove_uncertainty(self, value: str) -> None:
        if value in self.concept_uncertainties:
            self.concept_uncertainties.remove(value)

    # Métodos semânticos
    def is_oem(self) -> bool:
        return any(s in self.development_strategy for s in ["oem_pure", "white_label"])

    def is_adaptation(self) -> bool:
        return any(s in self.development_strategy for s in [
            "doc_adaptation",
            "tech_adaptation",
            "material_change",
            "process_change",
            "labeling_change",
        ])

    def is_inhouse(self) -> bool:
        return any(s in self.development_strategy for s in [
            "inhouse_production",
            "nationalization",
        ])

    def is_supplier_change(self) -> bool:
        return "supplier_change" in self.development_strategy

    def is_innovation(self) -> bool:
        return any(s in self.development_strategy for s in [
            "incremental_innovation",
            "radical_innovation",
            "platform",
        ])

    def is_radical(self) -> bool:
        return "radical_innovation" in self.development_strategy

    def is_platform(self) -> bool:
        return "platform" in self.development_strategy

    def is_kit_or_accessory(self) -> bool:
        return any(s in self.development_strategy for s in ["new_kit", "new_accessory"])

    def is_reference_based(self) -> bool:
        return any(s in self.development_strategy for s in [
            "similar_competitor",
            "doc_adaptation",
            "tech_adaptation",
            "material_change",
            "supplier_change",
            "nationalization",
            "new_kit",
            "new_accessory",
        ])

    def needs_concept_generation(self) -> bool:
        return any(s in self.development_strategy for s in [
            "incremental_innovation",
            "radical_innovation",
            "platform",
            "new_kit",
            "new_accessory",
            "similar_competitor",
            "tech_adaptation",
        ])

    def has_external_supplier(self) -> bool:
        return self.supplier_dependency in ["external_defined", "external_undefined"]

    def complexity_gte(self, level: ComplexityLevel) -> bool:
        return self.complexity.value >= level.value

    def is_simple_project(self) -> bool:
        is_only_oem = set(self.development_strategy) <= {
            "oem_pure",
            "white_label",
            "doc_adaptation",
        }
        return is_only_oem and self.complexity.value <= ComplexityLevel.LOW.value

    def compute_complexity(self) -> ComplexityLevel:
        bd: dict[str, int] = {}
        bd["Invasividade"] = self.invasiveness_level * 3
        bd["Maturidade Tecnológica"] = (3 - self.tech_maturity) * 2
        bd["Clareza do Problema"] = (2 - self.problem_clarity) * 2
        bd["Multi-stakeholder"] = int(self.multi_stakeholder) * 2
        bd["Componente Digital"] = int(self.has_digital_component) * 2
        bd["Esterilidade"] = int(self.sterility_required or self.sterility_unknown) * 2
        bd["Medicamento/Fluido Associado"] = int(self.has_associated_drug) * 3
        bd["Incerteza Regulatória"] = {
            "": 0,
            "none": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
        }.get(self.regulatory_uncertainty, 0) * 2
        bd["Incertezas de Conceito"] = len(self.concept_uncertainties)
        bd["Fornecedor Indefinido"] = int(self.supplier_dependency == "external_undefined") * 2
        bd["Inovação Radical"] = int(self.is_radical()) * 3
        bd["Plataforma"] = int(self.is_platform()) * 2

        self.score_breakdown = bd
        self.complexity_score = sum(bd.values())

        if self.complexity_score <= 5:
            self.complexity = ComplexityLevel.LOW
        elif self.complexity_score <= 12:
            self.complexity = ComplexityLevel.MEDIUM
        elif self.complexity_score <= 20:
            self.complexity = ComplexityLevel.HIGH
        else:
            self.complexity = ComplexityLevel.ULTRA

        return self.complexity


# =============================================================================
# FERRAMENTAS E REGRAS
# =============================================================================

@dataclass
class Tool:
    id: str
    name: str
    category: ToolCategory
    description: str


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


# =============================================================================
# BIBLIOTECA DE FERRAMENTAS
# =============================================================================

TOOL_LIBRARY: dict[str, Tool] = {t.id: t for t in [
    # OEM / Fornecedor
    Tool("OEM01", "Checklist de Produto OEM", ToolCategory.OEM_SUPPLIER,
         "Lista de verificação completa para produtos fornecidos por fabricante externo."),
    Tool("OEM02", "Avaliação Técnica de Fornecedor", ToolCategory.OEM_SUPPLIER,
         "Análise das capacidades técnicas, processos, histórico, qualidade e suporte do fornecedor."),
    Tool("OEM03", "Avaliação Documental de Fornecedor", ToolCategory.OEM_SUPPLIER,
         "Revisão de certificações, registros, documentação técnica, IFU, rotulagem e evidências do fabricante."),
    Tool("OEM04", "Comparação entre Fornecedores", ToolCategory.OEM_SUPPLIER,
         "Matriz comparativa de fornecedores alternativos com critérios técnicos, regulatórios e comerciais."),
    Tool("OEM05", "Análise de Responsabilidade Assumida pela Empresa", ToolCategory.OEM_SUPPLIER,
         "Mapeamento do que a empresa assume legal, técnica e regulatoriamente ao usar marca própria ou registro próprio."),
    Tool("OEM06", "Análise de Customização Necessária", ToolCategory.OEM_SUPPLIER,
         "Levantamento das adaptações de marca, idioma, embalagem, IFU, acessórios e documentação para o mercado local."),
    Tool("OEM07", "Análise de Amostras Comerciais", ToolCategory.OEM_SUPPLIER,
         "Avaliação técnica, funcional, visual e documental de amostras recebidas do fornecedor."),
    Tool("OEM08", "Matriz Make or Buy", ToolCategory.OEM_SUPPLIER,
         "Análise de decisão entre fabricar internamente, comprar pronto ou co-desenvolver com fornecedor."),

    # Substituição / qualificação de fornecedor
    Tool("SUP01", "Análise de Qualificação de Fornecedor Alternativo", ToolCategory.SUPPLIER_CHANGE,
         "Avaliação técnica e documental do novo fornecedor para substituição estruturada."),
    Tool("SUP02", "Análise de Equivalência Técnica entre Fornecedores", ToolCategory.SUPPLIER_CHANGE,
         "Comparação de produto, componente, material, desempenho e documentação entre fornecedor atual e alternativo."),
    Tool("SUP03", "Avaliação de Impacto da Troca de Fornecedor", ToolCategory.SUPPLIER_CHANGE,
         "Análise do impacto da mudança em qualidade, regulatório, custo, prazo, embalagem, rotulagem e disponibilidade."),
    Tool("SUP04", "Plano de Transição de Fornecedor", ToolCategory.SUPPLIER_CHANGE,
         "Planejamento das etapas de qualificação, estoque, transição e aprovação antes de substituir fornecedor."),

    # Kit / acessório
    Tool("KIT01", "Análise de Composição do Kit", ToolCategory.KIT_ACCESSORY,
         "Levantamento e validação de todos os componentes, quantidades, fornecedores e funções do kit."),
    Tool("KIT02", "Análise Regulatória de Kit Médico", ToolCategory.KIT_ACCESSORY,
         "Avaliação do enquadramento regulatório do kit, composição, classe, responsabilidade e apresentação comercial."),
    Tool("KIT03", "Análise de Compatibilidade entre Componentes", ToolCategory.KIT_ACCESSORY,
         "Verificação da compatibilidade técnica, dimensional, de material, uso, esterilidade e embalagem entre itens do kit."),
    Tool("KIT04", "Análise de Embalagem e Rotulagem do Kit", ToolCategory.KIT_ACCESSORY,
         "Definição dos requisitos de embalagem, IFU, rotulagem, identificação e apresentação do kit."),
    Tool("KIT05", "Análise de Acessório — Compatibilidade com Produto Principal", ToolCategory.KIT_ACCESSORY,
         "Verificação da compatibilidade técnica, regulatória, funcional e documental do acessório com o produto base."),

    # Adaptação
    Tool("ADP01", "Análise de Equivalência com Produto de Mercado", ToolCategory.ADAPTATION,
         "Comparação técnica, funcional, clínica e regulatória entre o produto proposto e o produto de referência."),
    Tool("ADP02", "Análise de Impacto da Modificação", ToolCategory.ADAPTATION,
         "Avaliação de como a modificação afeta desempenho, segurança, usabilidade, regulatório e custo."),
    Tool("ADP03", "Comparativo Produto Referência × Conceito Proposto", ToolCategory.ADAPTATION,
         "Tabela lado a lado das diferenças técnicas, clínicas, regulatórias, comerciais e de uso."),
    Tool("ADP04", "Análise de Alteração de Material", ToolCategory.ADAPTATION,
         "Avaliação do impacto da mudança de material em biocompatibilidade, desempenho, esterilização, fabricação e custo."),
    Tool("ADP05", "Análise de Alteração de Embalagem", ToolCategory.ADAPTATION,
         "Avaliação do impacto da mudança de embalagem em proteção, estabilidade, transporte, esterilidade e vida útil."),
    Tool("ADP06", "Análise de Alteração de IFU/Rotulagem", ToolCategory.ADAPTATION,
         "Revisão das instruções de uso, rotulagem, simbologia e claims considerando o novo contexto de aplicação."),
    Tool("ADP07", "Justificativa Técnica da Adaptação", ToolCategory.ADAPTATION,
         "Documento formal que justifica tecnicamente a necessidade, adequação e limites da adaptação."),

    # Internalização
    Tool("INT01", "Análise de Internalização Produtiva", ToolCategory.INTERNALIZATION,
         "Estudo de viabilidade para produção própria de produto ou componente antes externo."),
    Tool("INT02", "Mapa de Processos Necessários", ToolCategory.INTERNALIZATION,
         "Levantamento de processos produtivos, controles, inspeções, infraestrutura e suporte necessários."),
    Tool("INT03", "Análise de Capacidade Instalada", ToolCategory.INTERNALIZATION,
         "Avaliação da infraestrutura atual versus recursos necessários para produção interna."),
    Tool("INT04", "Estimativa de Ferramental", ToolCategory.INTERNALIZATION,
         "Levantamento preliminar de moldes, gabaritos, dispositivos, ferramentas e equipamentos necessários."),
    Tool("INT05", "Estimativa de CAPEX/OPEX", ToolCategory.INTERNALIZATION,
         "Estimativa de investimento inicial, custos operacionais, manutenção e recursos de produção."),
    Tool("INT06", "Análise de Escala Produtiva", ToolCategory.INTERNALIZATION,
         "Avaliação de volume mínimo viável, capacidade, lote, produtividade e curva de escala."),
    Tool("INT07", "Análise de Nacionalização", ToolCategory.INTERNALIZATION,
         "Estudo de substituição de componentes importados por nacionais sem perda de qualidade, segurança ou desempenho."),

    # Regulatório e segurança preliminar
    Tool("REG01", "Classificação Regulatória Preliminar", ToolCategory.REGULATORY,
         "Triagem inicial da classe do dispositivo e caminho provável com base no uso pretendido."),
    Tool("REG02", "Definição do Uso Pretendido", ToolCategory.REGULATORY,
         "Declaração formal do propósito clínico, população-alvo, indicação e contexto de uso do produto."),
    Tool("REG03", "Definição do Usuário Pretendido", ToolCategory.REGULATORY,
         "Caracterização do perfil do usuário, competências esperadas, treinamento e restrições."),
    Tool("REG04", "Definição do Ambiente de Uso", ToolCategory.REGULATORY,
         "Descrição do ambiente clínico, hospitalar, ambulatorial, domiciliar, laboratorial ou produtivo onde será utilizado."),
    Tool("REG05", "Análise Preliminar de Claims", ToolCategory.REGULATORY,
         "Triagem das alegações clínicas, técnicas ou comerciais que o produto poderá fazer e quais evidências serão necessárias."),
    Tool("REG06", "Mapa de Normas Aplicáveis", ToolCategory.REGULATORY,
         "Levantamento preliminar de normas técnicas, guias, requisitos regulatórios e boas práticas aplicáveis."),
    Tool("REG07", "Triagem de Biocompatibilidade", ToolCategory.REGULATORY,
         "Avaliação preliminar da necessidade de testes de biocompatibilidade conforme contato, material e duração."),
    Tool("REG08", "Triagem de Esterilidade e Processo de Esterilização", ToolCategory.REGULATORY,
         "Avaliação preliminar da necessidade de esterilidade, método possível e impacto no conceito."),
    Tool("REG09", "Triagem de Embalagem e Vida Útil", ToolCategory.REGULATORY,
         "Análise preliminar de embalagem, barreira estéril, armazenamento, transporte, estabilidade e prazo de validade."),
    Tool("REG10", "Análise de Impacto Regulatório Preliminar", ToolCategory.REGULATORY,
         "Avaliação do impacto regulatório das decisões de conceito antes do projeto formal."),

    # Pesquisa de necessidade
    Tool("NED01", "Voice of Customer (VoC)", ToolCategory.NEED_RESEARCH,
         "Captura sistemática das necessidades reais do usuário clínico, técnico, comprador ou paciente."),
    Tool("NED02", "Persona Clínica", ToolCategory.NEED_RESEARCH,
         "Perfil detalhado do usuário pretendido: médico, paciente, técnico, enfermeiro, comprador ou equipe interna."),
    Tool("NED03", "Jornada do Usuário/Paciente", ToolCategory.NEED_RESEARCH,
         "Mapeamento da experiência completa antes, durante e depois do uso do produto."),
    Tool("NED04", "Observação Etnográfica", ToolCategory.NEED_RESEARCH,
         "Estudo do uso real em ambiente hospitalar, clínico, produtivo ou domiciliar."),
    Tool("NED05", "Entrevista com KOL", ToolCategory.NEED_RESEARCH,
         "Consulta estruturada a especialistas clínicos para validar necessidade, contexto e relevância do conceito."),
    Tool("NED06", "Gap Analysis", ToolCategory.NEED_RESEARCH,
         "Comparação entre estado atual, necessidade não atendida e estado desejado para orientar o escopo do conceito."),

    # Ideação
    Tool("IDE01", "Brainstorming Estruturado", ToolCategory.IDEATION,
         "Geração livre de ideias com critérios de foco clínico, técnico, regulatório e comercial."),
    Tool("IDE02", "SCAMPER", ToolCategory.IDEATION,
         "Substituir, Combinar, Adaptar, Modificar, Propor outros usos, Eliminar e Reorganizar soluções."),
    Tool("IDE03", "Mapa Mental", ToolCategory.IDEATION,
         "Organização visual de ideias, restrições, alternativas, riscos e conexões do conceito."),
    Tool("IDE04", "TRIZ", ToolCategory.IDEATION,
         "Método para resolver contradições técnicas e gerar soluções inventivas."),
    Tool("IDE05", "Analogia Biônica", ToolCategory.IDEATION,
         "Inspiração em soluções da natureza para resolver desafios técnicos de design médico."),
    Tool("IDE06", "Matriz Morfológica", ToolCategory.IDEATION,
         "Combinação sistemática de subfunções e subsoluções para gerar conceitos alternativos."),
    Tool("IDE07", "Design Thinking — Ciclo Completo", ToolCategory.IDEATION,
         "Processo centrado no usuário: empatia, definição, ideação, protótipo e teste de conceito."),
    Tool("IDE08", "Canvas da Oportunidade Médica", ToolCategory.IDEATION,
         "Estruturação visual da oportunidade clínica, mercado, usuário, solução, diferencial e viabilidade."),

    # Mercado e tecnologia
    Tool("MKT01", "Benchmarking Competitivo", ToolCategory.MARKET_TECH,
         "Análise sistemática de produtos concorrentes, similares, substitutos e referências de mercado."),
    Tool("MKT02", "Patent Mapping", ToolCategory.MARKET_TECH,
         "Mapeamento preliminar de patentes para identificar riscos, espaços livres e oportunidades de diferenciação."),
    Tool("MKT03", "Avaliação de Maturidade Tecnológica (TRL)", ToolCategory.MARKET_TECH,
         "Avaliação do nível de prontidão tecnológica e das incertezas técnicas antes de virar projeto formal."),
    Tool("MKT04", "Análise SWOT do Produto", ToolCategory.MARKET_TECH,
         "Forças, fraquezas, oportunidades e ameaças do conceito em desenvolvimento."),
    Tool("MKT05", "Análise de Custo Unitário", ToolCategory.MARKET_TECH,
         "Estimativa preliminar de custo unitário, custo-alvo, margem e viabilidade econômica."),
    Tool("MKT06", "Matriz Go/No-Go", ToolCategory.MARKET_TECH,
         "Critérios objetivos para decisão de avançar, pausar, descartar ou aprofundar o conceito."),

    # Requisitos conceituais
    Tool("REQ01", "Lista Preliminar de Necessidades e Requisitos Conceituais", ToolCategory.REQUIREMENTS,
         "Compilação inicial das necessidades do usuário e requisitos de alto nível para orientar o projeto futuro."),
    Tool("REQ02", "User Needs Statement", ToolCategory.REQUIREMENTS,
         "Declaração estruturada das necessidades do usuário em formato claro, rastreável e não ambíguo."),
    Tool("REQ03", "CTQ Preliminar — Critical to Quality", ToolCategory.REQUIREMENTS,
         "Identificação preliminar dos atributos críticos de qualidade, segurança, desempenho e uso."),
    Tool("REQ04", "QFD Conceitual — Casa da Qualidade", ToolCategory.REQUIREMENTS,
         "Tradução conceitual das necessidades do usuário em características técnicas de alto nível."),

    # Seleção e aprovação
    Tool("CON01", "Pugh Matrix", ToolCategory.CONCEPT_APPROVAL,
         "Seleção e comparação sistemática de conceitos alternativos usando referência e critérios ponderados."),
    Tool("CON02", "Gate de Conceito / Aprovação da Oportunidade", ToolCategory.CONCEPT_APPROVAL,
         "Revisão formal com critérios de aprovação, pendências e decisão antes de passar ao time de projeto."),
    Tool("CON03", "Business Case Preliminar", ToolCategory.CONCEPT_APPROVAL,
         "Avaliação de viabilidade técnica, comercial, regulatória, econômica e estratégica do conceito proposto."),
    Tool("CON04", "Delphi Method", ToolCategory.CONCEPT_APPROVAL,
         "Consenso estruturado entre especialistas para validar conceitos complexos ou sem precedente direto."),
    Tool("CON05", "Prototipagem de Conceito", ToolCategory.CONCEPT_APPROVAL,
         "Representação visual, física ou digital mínima para validar premissas e comunicar o conceito."),

    # Entregáveis
    Tool("OUT01", "One-Page Concept", ToolCategory.DELIVERABLES,
         "Resumo executivo de uma página com a essência do conceito aprovado."),
    Tool("OUT02", "Relatório de Conceito (Concept Report)", ToolCategory.DELIVERABLES,
         "Documento formal que consolida o ciclo de idealização, análise e seleção do conceito."),
    Tool("OUT03", "Lista de Premissas", ToolCategory.DELIVERABLES,
         "Registro das premissas assumidas durante a construção, análise e aprovação do conceito."),
    Tool("OUT04", "Lista de Incertezas Abertas", ToolCategory.DELIVERABLES,
         "Registro das questões não resolvidas que o time de projeto deverá endereçar."),
    Tool("OUT05", "Lista de Recomendações para a Próxima Fase", ToolCategory.DELIVERABLES,
         "Orientações específicas para o time de projeto com base nas decisões e pendências do conceito."),
    Tool("OUT06", "Termo de Conceito Aprovado", ToolCategory.DELIVERABLES,
         "Documento formal de aprovação para passagem ao time de projeto."),
    Tool("OUT07", "Pacote de Transferência para Projeto", ToolCategory.DELIVERABLES,
         "Compilação dos documentos, dados, decisões, premissas e incertezas para handoff ao time de projeto."),
]}


# =============================================================================
# HELPERS DAS REGRAS
# =============================================================================

def _prio(mandatory_if: Callable[[ProjectProfile], bool], p: ProjectProfile) -> ToolPriority:
    return ToolPriority.MANDATORY if mandatory_if(p) else ToolPriority.RECOMMENDED


def _simple_prio(mandatory_if: Callable[[ProjectProfile], bool], p: ProjectProfile) -> ToolPriority:
    if p.is_simple_project():
        return ToolPriority.OPTIONAL
    return ToolPriority.MANDATORY if mandatory_if(p) else ToolPriority.RECOMMENDED


# =============================================================================
# REGRAS DE ATIVAÇÃO DAS FERRAMENTAS
# =============================================================================

RULES: list[ToolRule] = [
    # OEM / fornecedor
    ToolRule("OEM01",
        condition=lambda p: p.is_oem(),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Produto será fornecido por fabricante externo — checklist de produto OEM é obrigatório."),

    ToolRule("OEM02",
        condition=lambda p: ((p.has_external_supplier() and not p.is_supplier_change()) or p.is_oem()),
        priority_fn=lambda p: _prio(lambda p: p.supplier_dependency == "external_undefined", p),
        reason_fn=lambda p: (
            "Fornecedor ainda não definido — avaliação técnica é crítica para seleção."
            if p.supplier_dependency == "external_undefined"
            else "Fornecedor externo identificado — avaliação técnica recomendada para qualificação."
        )),

    ToolRule("OEM03",
        condition=lambda p: p.has_external_supplier() and "regulatory_holder" in p.company_responsibility,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Empresa assumirá titularidade regulatória — avaliação documental do fabricante é obrigatória."),

    ToolRule("OEM04",
        condition=lambda p: p.has_multiple_suppliers and not p.is_supplier_change(),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Múltiplos fornecedores identificados — comparação estruturada é obrigatória."),

    ToolRule("OEM05",
        condition=lambda p: "brand_owner" in p.company_responsibility or "regulatory_holder" in p.company_responsibility,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Empresa assumirá marca e/ou titularidade regulatória — análise de responsabilidade é obrigatória."),

    ToolRule("OEM06",
        condition=lambda p: p.is_oem() and (p.labeling_change_required or p.ifu_change_required or p.packaging_change_required),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Customização local necessária no produto OEM — análise de escopo de adaptação obrigatória."),

    ToolRule("OEM07",
        condition=lambda p: p.has_external_supplier() and not p.is_supplier_change(),
        priority_fn=lambda p: _prio(lambda p: p.has_patient_contact and p.sterility_required, p),
        reason_fn=lambda p: "Produto externo com contato ou esterilidade — análise de amostras necessária antes da decisão."),

    ToolRule("OEM08",
        condition=lambda p: p.is_oem() or p.is_inhouse(),
        priority_fn=lambda p: _prio(lambda p: p.cost_is_critical, p),
        reason_fn=lambda p: "Decisão entre fabricar ou comprar é estrutural para este conceito."),

    # Substituição de fornecedor
    ToolRule("SUP01",
        condition=lambda p: p.is_supplier_change(),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Substituição de fornecedor identificada — qualificação estruturada do alternativo é obrigatória."),

    ToolRule("SUP02",
        condition=lambda p: p.is_supplier_change(),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Equivalência técnica entre fornecedores deve ser comprovada antes da troca."),

    ToolRule("SUP03",
        condition=lambda p: p.is_supplier_change(),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Impacto da troca de fornecedor em qualidade, custo e regulatório deve ser avaliado no conceito."),

    ToolRule("SUP04",
        condition=lambda p: p.is_supplier_change(),
        priority_fn=lambda p: _prio(lambda p: p.complexity_gte(ComplexityLevel.MEDIUM), p),
        reason_fn=lambda p: "Plano de transição estruturado necessário para troca sem descontinuidade de produto."),

    # Kit / acessório
    ToolRule("KIT01",
        condition=lambda p: "new_kit" in p.development_strategy,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Novo kit — levantamento e validação da composição é obrigatório antes de avançar."),

    ToolRule("KIT02",
        condition=lambda p: p.is_kit_or_accessory(),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Kit ou acessório médico pode ter enquadramento regulatório distinto — análise regulatória específica obrigatória."),

    ToolRule("KIT03",
        condition=lambda p: "new_kit" in p.development_strategy,
        priority_fn=lambda p: _prio(lambda p: p.has_patient_contact or p.sterility_required, p),
        reason_fn=lambda p: (
            "Kit com contato com paciente ou estéril — compatibilidade entre componentes é crítica."
            if p.has_patient_contact or p.sterility_required
            else "Compatibilidade entre componentes do kit recomendada antes do conceito final."
        )),

    ToolRule("KIT04",
        condition=lambda p: p.is_kit_or_accessory(),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Kit/acessório exige análise específica de embalagem, rotulagem e IFU."),

    ToolRule("KIT05",
        condition=lambda p: "new_accessory" in p.development_strategy,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Novo acessório — compatibilidade técnica e regulatória com o produto principal é obrigatória."),

    # Adaptação
    ToolRule("ADP01",
        condition=lambda p: ((p.is_adaptation() and p.has_existing_reference)
                             or "similar_competitor" in p.development_strategy
                             or p.has_similar_registration),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: (
            "Existe produto de referência ou registro similar — análise de equivalência é obrigatória."
            if p.has_similar_registration else
            "Produto similar a concorrente ou adaptação com referência — análise de equivalência é obrigatória."
        )),

    ToolRule("ADP02",
        condition=lambda p: p.is_adaptation(),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Modificação planejada — análise de impacto em segurança, desempenho e regulatório é obrigatória."),

    ToolRule("ADP03",
        condition=lambda p: p.is_reference_based(),
        priority_fn=lambda p: _prio(lambda p: "similar_competitor" in p.development_strategy, p),
        reason_fn=lambda p: "Comparativo estruturado produto referência × conceito proposto facilita decisão e documentação."),

    ToolRule("ADP04",
        condition=lambda p: "material_change" in p.development_strategy,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Alteração de material identificada — análise de impacto em biocompatibilidade e desempenho é obrigatória."),

    ToolRule("ADP05",
        condition=lambda p: p.packaging_change_required or "material_change" in p.development_strategy,
        priority_fn=lambda p: _prio(lambda p: p.sterility_required or p.sterility_unknown, p),
        reason_fn=lambda p: "Alteração de embalagem prevista — avaliação de impacto em proteção e esterilidade necessária."),

    ToolRule("ADP06",
        condition=lambda p: p.labeling_change_required or p.ifu_change_required or "new_kit" in p.development_strategy,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Alteração de IFU/rotulagem ou novo kit — revisão formal é obrigatória."),

    ToolRule("ADP07",
        condition=lambda p: p.is_adaptation(),
        priority_fn=lambda p: ToolPriority.RECOMMENDED,
        reason_fn=lambda p: "Justificativa técnica da adaptação é base para documentação regulatória futura."),

    # Internalização
    ToolRule("INT01",
        condition=lambda p: p.is_inhouse(),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Estratégia de internalização identificada — análise de viabilidade produtiva é obrigatória."),

    ToolRule("INT02",
        condition=lambda p: p.is_inhouse(),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Produção própria exige mapeamento completo dos processos necessários."),

    ToolRule("INT03",
        condition=lambda p: p.is_inhouse(),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Avaliação da capacidade instalada é pré-requisito para decisão de internalizar."),

    ToolRule("INT04",
        condition=lambda p: p.is_inhouse() and p.complexity_gte(ComplexityLevel.MEDIUM),
        priority_fn=lambda p: ToolPriority.RECOMMENDED,
        reason_fn=lambda p: "Estimativa de ferramental necessária para compor o Business Case da internalização."),

    ToolRule("INT05",
        condition=lambda p: p.is_inhouse(),
        priority_fn=lambda p: _prio(lambda p: p.cost_is_critical, p),
        reason_fn=lambda p: "Estimativa de CAPEX/OPEX necessária para validar viabilidade econômica da internalização."),

    ToolRule("INT06",
        condition=lambda p: p.is_inhouse() and p.complexity_gte(ComplexityLevel.MEDIUM),
        priority_fn=lambda p: ToolPriority.RECOMMENDED,
        reason_fn=lambda p: "Análise de escala produtiva relevante para avaliar rentabilidade mínima."),

    ToolRule("INT07",
        condition=lambda p: "nationalization" in p.development_strategy,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Projeto de nacionalização identificado — análise específica é obrigatória."),

    # Regulatório
    ToolRule("REG01",
        condition=lambda p: True,
        priority_fn=lambda p: _prio(
            lambda p: not p.has_regulatory_class or p.regulatory_uncertainty in ["medium", "high"],
            p
        ),
        reason_fn=lambda p: (
            "Classe regulatória não confirmada — triagem preliminar é obrigatória antes de avançar."
            if not p.has_regulatory_class else
            "Triagem regulatória recomendada para validar enquadramento do conceito."
        )),

    ToolRule("REG02",
        condition=lambda p: True,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Definição do uso pretendido é base de toda a documentação regulatória e do conceito."),

    ToolRule("REG03",
        condition=lambda p: True,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Definição do usuário pretendido é obrigatória para usabilidade e regulatório."),

    ToolRule("REG04",
        condition=lambda p: True,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Definição do ambiente de uso é obrigatória para concepção segura do produto."),

    ToolRule("REG05",
        condition=lambda p: (
            p.is_innovation()
            or "similar_competitor" in p.development_strategy
            or p.has_associated_drug
            or p.complexity_gte(ComplexityLevel.MEDIUM)
        ),
        priority_fn=lambda p: _prio(lambda p: p.is_radical() or p.has_associated_drug, p),
        reason_fn=lambda p: "Análise preliminar de claims orienta o escopo clínico, técnico e regulatório do conceito."),

    ToolRule("REG06",
        condition=lambda p: True,
        priority_fn=lambda p: _prio(lambda p: not p.norm_identified, p),
        reason_fn=lambda p: (
            "Normas aplicáveis não identificadas — mapeamento é obrigatório para continuar."
            if not p.norm_identified else
            "Mapeamento de normas recomendado para documentar o escopo regulatório."
        )),

    ToolRule("REG07",
        condition=lambda p: p.has_patient_contact or "material_change" in p.development_strategy,
        priority_fn=lambda p: _prio(
            lambda p: p.invasiveness_level >= 2 or "material_change" in p.development_strategy,
            p
        ),
        reason_fn=lambda p: (
            "Produto invasivo ou com alteração de material — triagem de biocompatibilidade é obrigatória."
            if p.invasiveness_level >= 2 or "material_change" in p.development_strategy else
            "Contato com paciente identificado — triagem de biocompatibilidade recomendada."
        )),

    ToolRule("REG08",
        condition=lambda p: p.sterility_required or p.sterility_unknown or "sterility" in p.concept_uncertainties,
        priority_fn=lambda p: _prio(lambda p: p.sterility_required, p),
        reason_fn=lambda p: (
            "Produto estéril — triagem de processo de esterilização é obrigatória no conceito."
            if p.sterility_required else
            "Esterilidade indefinida — triagem recomendada para evitar retrabalho no projeto."
        )),

    ToolRule("REG09",
        condition=lambda p: p.sterility_required or p.sterility_unknown or p.packaging_change_required,
        priority_fn=lambda p: _prio(lambda p: p.sterility_required, p),
        reason_fn=lambda p: "Produto estéril, esterilidade indefinida ou mudança de embalagem — triagem de embalagem e vida útil necessária."),

    ToolRule("REG10",
        condition=lambda p: (
            p.regulatory_uncertainty in ["medium", "high"]
            or not p.has_regulatory_class
            or "new_kit" in p.development_strategy
            or p.has_similar_registration
            or p.has_associated_drug
        ),
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Incerteza, kit, similar registrado ou substância associada — análise de impacto regulatório obrigatória."),

    # Pesquisa de necessidade
    ToolRule("NED01",
        condition=lambda p: p.needs_concept_generation() or p.problem_clarity < 2,
        priority_fn=lambda p: _prio(lambda p: p.is_innovation() or p.problem_clarity == 0, p),
        reason_fn=lambda p: "Produto exige ideação ativa ou problema ainda não definido — VoC é necessário."),

    ToolRule("NED02",
        condition=lambda p: p.needs_concept_generation() or p.multi_stakeholder or p.user_type in ["patient_or_caregiver", "multiple_users"],
        priority_fn=lambda p: _prio(lambda p: p.is_radical() or p.is_platform(), p),
        reason_fn=lambda p: "Produto novo, múltiplos perfis ou usuário crítico — Persona Clínica é relevante."),

    ToolRule("NED03",
        condition=lambda p: p.needs_concept_generation() or p.multi_stakeholder or p.complexity_gte(ComplexityLevel.HIGH),
        priority_fn=lambda p: _prio(lambda p: p.is_radical() or p.is_platform(), p),
        reason_fn=lambda p: "Jornada do usuário orienta decisões de conceito e validação clínica."),

    ToolRule("NED04",
        condition=lambda p: p.is_innovation() and not p.has_field_observation,
        priority_fn=lambda p: _prio(lambda p: p.is_radical(), p),
        reason_fn=lambda p: "Inovação sem observação de campo — visita etnográfica necessária."),

    ToolRule("NED05",
        condition=lambda p: p.is_innovation() or p.invasiveness_level >= 2,
        priority_fn=lambda p: _prio(lambda p: p.is_radical() or p.is_platform(), p),
        reason_fn=lambda p: "Produto inovador ou invasivo — validação com KOL é fundamental para o conceito."),

    ToolRule("NED06",
        condition=lambda p: True,
        priority_fn=lambda p: _prio(lambda p: p.problem_clarity < 2, p),
        reason_fn=lambda p: "Gap Analysis orienta o escopo do problema e valida a necessidade do produto."),

    # Ideação
    ToolRule("IDE01",
        condition=lambda p: p.needs_concept_generation() or p.problem_clarity < 2,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Fase de ideação necessária — brainstorming estruturado é ponto de partida obrigatório."),

    ToolRule("IDE02",
        condition=lambda p: p.is_adaptation() or p.is_kit_or_accessory() or "incremental_innovation" in p.development_strategy,
        priority_fn=lambda p: ToolPriority.RECOMMENDED,
        reason_fn=lambda p: "SCAMPER é útil para adaptações, kits, acessórios e inovações incrementais."),

    ToolRule("IDE03",
        condition=lambda p: p.needs_concept_generation(),
        priority_fn=lambda p: ToolPriority.RECOMMENDED,
        reason_fn=lambda p: "Mapa Mental ajuda a organizar ideias e conexões do conceito."),

    ToolRule("IDE04",
        condition=lambda p: p.is_radical() or p.complexity_gte(ComplexityLevel.HIGH),
        priority_fn=lambda p: _prio(lambda p: p.is_radical(), p),
        reason_fn=lambda p: "TRIZ aplicável em problemas complexos com contradições técnicas."),

    ToolRule("IDE05",
        condition=lambda p: p.is_radical() or p.is_platform(),
        priority_fn=lambda p: ToolPriority.OPTIONAL,
        reason_fn=lambda p: "Analogia Biônica pode inspirar soluções inovadoras de design médico."),

    ToolRule("IDE06",
        condition=lambda p: p.needs_concept_generation() and p.complexity_gte(ComplexityLevel.MEDIUM),
        priority_fn=lambda p: _prio(lambda p: p.is_radical() or p.is_platform(), p),
        reason_fn=lambda p: "Matriz Morfológica estrutura geração sistemática de conceitos alternativos."),

    ToolRule("IDE07",
        condition=lambda p: p.is_radical() or p.is_platform(),
        priority_fn=lambda p: _prio(lambda p: p.is_radical(), p),
        reason_fn=lambda p: "Design Thinking completo recomendado para inovações radicais e plataformas."),

    ToolRule("IDE08",
        condition=lambda p: p.needs_concept_generation() or p.is_oem() or p.is_supplier_change(),
        priority_fn=lambda p: _prio(lambda p: p.is_innovation(), p),
        reason_fn=lambda p: "Canvas da Oportunidade estrutura a proposta de valor do conceito."),

    # Mercado e tecnologia
    ToolRule("MKT01",
        condition=lambda p: True,
        priority_fn=lambda p: _prio(
            lambda p: p.is_oem() or p.is_adaptation() or p.is_inhouse() or "similar_competitor" in p.development_strategy,
            p
        ),
        reason_fn=lambda p: "Benchmarking competitivo é base para posicionamento do conceito no mercado."),

    ToolRule("MKT02",
        condition=lambda p: p.is_innovation() or "similar_competitor" in p.development_strategy or p.complexity_gte(ComplexityLevel.MEDIUM),
        priority_fn=lambda p: _prio(
            lambda p: p.is_radical() or p.is_platform() or "similar_competitor" in p.development_strategy,
            p
        ),
        reason_fn=lambda p: "Mapeamento de patentes recomendado para garantir espaço livre de IP antes de avançar."),

    ToolRule("MKT03",
        condition=lambda p: p.is_innovation() and p.tech_maturity <= 2,
        priority_fn=lambda p: _prio(lambda p: p.tech_maturity <= 1, p),
        reason_fn=lambda p: "Tecnologia não consolidada — avaliação de maturidade tecnológica necessária."),

    ToolRule("MKT04",
        condition=lambda p: True,
        priority_fn=lambda p: ToolPriority.RECOMMENDED,
        reason_fn=lambda p: "Análise SWOT orienta decisões estratégicas ao longo do conceito."),

    ToolRule("MKT05",
        condition=lambda p: p.cost_is_critical or p.is_oem() or p.is_inhouse() or p.is_supplier_change(),
        priority_fn=lambda p: _prio(lambda p: p.cost_is_critical, p),
        reason_fn=lambda p: "Custo é fator relevante — estimativa de custo unitário necessária para decisão de conceito."),

    ToolRule("MKT06",
        condition=lambda p: p.complexity_gte(ComplexityLevel.MEDIUM) or p.regulatory_uncertainty in ["medium", "high"],
        priority_fn=lambda p: _prio(lambda p: p.complexity_gte(ComplexityLevel.HIGH), p),
        reason_fn=lambda p: "Complexidade ou incerteza elevada — Matriz Go/No-Go estrutura a decisão de avançar."),

    # Requisitos conceituais
    ToolRule("REQ01",
        condition=lambda p: True,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Lista preliminar de requisitos é obrigatória em qualquer conceito de produto médico."),

    ToolRule("REQ02",
        condition=lambda p: p.needs_concept_generation() or p.has_patient_contact,
        priority_fn=lambda p: _prio(lambda p: p.needs_concept_generation(), p),
        reason_fn=lambda p: "User Needs Statement formaliza as necessidades do usuário antes da geração de conceitos."),

    ToolRule("REQ03",
        condition=lambda p: p.needs_concept_generation() or p.complexity_gte(ComplexityLevel.MEDIUM),
        priority_fn=lambda p: _prio(lambda p: p.is_radical() or p.is_platform(), p),
        reason_fn=lambda p: "CTQ Preliminar define parâmetros críticos que o conceito deve atender."),

    ToolRule("REQ04",
        condition=lambda p: p.is_innovation() and p.complexity_gte(ComplexityLevel.HIGH),
        priority_fn=lambda p: _prio(lambda p: p.multi_stakeholder or p.is_platform(), p),
        reason_fn=lambda p: "QFD Conceitual traduz necessidades em especificações em produtos complexos."),

    # Seleção e aprovação
    ToolRule("CON01",
        condition=lambda p: p.needs_concept_generation() or p.is_inhouse() or p.is_adaptation(),
        priority_fn=lambda p: _prio(lambda p: p.complexity_gte(ComplexityLevel.MEDIUM), p),
        reason_fn=lambda p: "Pugh Matrix estrutura comparação entre conceitos alternativos antes da aprovação."),

    ToolRule("CON02",
        condition=lambda p: True,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Gate de Conceito é obrigatório para formalizar aprovação antes de passar ao projeto."),

    ToolRule("CON03",
        condition=lambda p: True,
        priority_fn=lambda p: _prio(
            lambda p: p.cost_is_critical or p.is_inhouse() or p.is_oem() or p.complexity_gte(ComplexityLevel.MEDIUM),
            p
        ),
        reason_fn=lambda p: "Business Case preliminar valida viabilidade técnica e comercial antes de investir no projeto."),

    ToolRule("CON04",
        condition=lambda p: p.is_radical() or p.is_platform() or p.complexity_gte(ComplexityLevel.HIGH),
        priority_fn=lambda p: ToolPriority.RECOMMENDED,
        reason_fn=lambda p: "Delphi Method útil para consenso em conceitos complexos ou sem precedente."),

    ToolRule("CON05",
        condition=lambda p: p.needs_concept_generation() or p.complexity_gte(ComplexityLevel.MEDIUM),
        priority_fn=lambda p: _prio(lambda p: p.needs_concept_generation(), p),
        reason_fn=lambda p: "Prototipagem de conceito valida premissas críticas antes do projeto formal."),

    # Entregáveis
    ToolRule("OUT01",
        condition=lambda p: True,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "One-Page Concept é o resumo executivo do conceito para comunicação interna."),

    ToolRule("OUT02",
        condition=lambda p: True,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Concept Report é o documento formal de saída deste ciclo de idealização."),

    ToolRule("OUT03",
        condition=lambda p: True,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Lista de premissas é obrigatória para rastreabilidade das decisões do conceito."),

    ToolRule("OUT04",
        condition=lambda p: True,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Lista de incertezas abertas é obrigatória para o time de projeto priorizar investigações."),

    ToolRule("OUT05",
        condition=lambda p: True,
        priority_fn=lambda p: _simple_prio(lambda p: p.complexity_gte(ComplexityLevel.MEDIUM), p),
        reason_fn=lambda p: "Recomendações orientam o time de projeto nas decisões críticas da próxima fase."),

    ToolRule("OUT06",
        condition=lambda p: p.needs_internal_approval,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Aprovação interna formal necessária — Termo de Conceito Aprovado é obrigatório."),

    ToolRule("OUT07",
        condition=lambda p: True,
        priority_fn=lambda p: ToolPriority.MANDATORY,
        reason_fn=lambda p: "Pacote de transferência garante handoff completo e rastreável ao time de projeto."),
]


# =============================================================================
# QUESTIONÁRIO ADAPTATIVO
# =============================================================================

@dataclass
class Question:
    id: str
    text: str
    options: dict[str, str]
    handler: Callable[[str | list[str], ProjectProfile], list[str]]
    multiple: bool = False
    exclusive_options: set[str] = field(default_factory=set)
    help_text: str = ""


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

        next_qs = [
            "Q03",
            "Q_USER1",
            "Q04",
            "Q05",
            "Q_REG1",
            "Q_REG2",
            "Q_REG3",
        ]

        if p.is_oem():
            next_qs += ["Q_OEM1", "Q_OEM2", "Q_OEM3"]
        if p.is_supplier_change():
            next_qs += ["Q_SUP1"]
        if p.is_adaptation():
            next_qs += ["Q_ADP1", "Q_ADP2"]
        if p.is_kit_or_accessory():
            next_qs += ["Q_KIT1"]
        if "similar_competitor" in p.development_strategy:
            next_qs += ["Q_SIM1"]
        if p.is_inhouse():
            next_qs += ["Q_INT1"]
        if p.is_innovation():
            next_qs += ["Q_INN1", "Q_INN2"]

        next_qs += [
            "Q_CROSS1",
            "Q_CROSS2",
            "Q_CROSS3",
            "Q_CROSS4",
            "Q_CROSS5",
            "Q_CROSS6",
            "Q_FINAL",
        ]
        return next_qs

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
        return []

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
        return []

    def h_patient_contact(v: str, p: ProjectProfile) -> list[str]:
        p.invasiveness_level = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}[v]
        p.has_patient_contact = v != "A"
        return []

    def h_sterility(v: str, p: ProjectProfile) -> list[str]:
        p.sterility_required = v == "A"
        p.sterility_unknown = v == "C"
        if v == "C":
            p.add_uncertainty("sterility")
            p.packaging_change_required = True
        else:
            p.remove_uncertainty("sterility")
        return []

    def h_reg1(v: str, p: ProjectProfile) -> list[str]:
        p.has_regulatory_class = v == "A"
        p.regulatory_uncertainty = {"A": "low", "B": "medium", "C": "high"}[v]
        return []

    def h_reg2(v: str, p: ProjectProfile) -> list[str]:
        p.has_similar_registration = v == "A"
        return []

    def h_reg3(v: str, p: ProjectProfile) -> list[str]:
        p.norm_identified = v == "A"
        return []

    def h_oem1(v: str, p: ProjectProfile) -> list[str]:
        p.supplier_dependency = {
            "A": "external_defined",
            "B": "external_undefined",
            "C": "external_undefined",
        }[v]
        p.has_multiple_suppliers = v == "C"
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
        return []

    def h_oem3(v: str, p: ProjectProfile) -> list[str]:
        p.cost_is_critical = v in ("A", "B")
        return []

    def h_sup1(v: str, p: ProjectProfile) -> list[str]:
        p.supplier_dependency = "external_undefined" if v in ("B", "C") else "external_defined"
        p.has_multiple_suppliers = v == "C"
        return []

    def h_adp1(vs: list[str], p: ProjectProfile) -> list[str]:
        if "C" in vs and "material_change" not in p.development_strategy:
            p.development_strategy.append("material_change")
        if "D" in vs:
            p.packaging_change_required = True
        if "E" in vs:
            p.labeling_change_required = True
            p.ifu_change_required = True
        if "F" in vs and "process_change" not in p.development_strategy:
            p.development_strategy.append("process_change")
        if "B" in vs:
            p.add_uncertainty("regulatory")
        return []

    def h_adp2(v: str, p: ProjectProfile) -> list[str]:
        p.has_existing_reference = v in ("A", "B")
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
        if "D" in vs:
            p.ifu_change_required = True
        if "E" in vs:
            p.has_existing_reference = True
        return []

    def h_sim1(v: str, p: ProjectProfile) -> list[str]:
        p.has_existing_reference = True
        p.reference_is_competitor = True
        return []

    def h_int1(v: str, p: ProjectProfile) -> list[str]:
        p.manufacturing_strategy = "inhouse"
        if v == "C":
            p.sterility_required = True
            p.sterility_unknown = False
            p.remove_uncertainty("sterility")
        if v == "D":
            p.add_uncertainty("manufacturing")
        return []

    def h_inn1(v: str, p: ProjectProfile) -> list[str]:
        p.tech_maturity = {"A": 3, "B": 2, "C": 1, "D": 0}[v]
        return []

    def h_inn2(vs: list[str], p: ProjectProfile) -> list[str]:
        imap = {
            "A": "clinical_evidence",
            "B": "ip_space",
            "C": "technology",
            "D": "supplier",
            "E": "regulatory",
            "F": "cost",
            "G": "manufacturing",
        }
        for v in vs:
            if v in imap:
                p.add_uncertainty(imap[v])
        return []

    def h_cross1(v: str, p: ProjectProfile) -> list[str]:
        p.problem_clarity = {"A": 2, "B": 1, "C": 0}[v]
        return []

    def h_cross2(v: str, p: ProjectProfile) -> list[str]:
        p.multi_stakeholder = v == "A" or p.user_type == "multiple_users"
        return []

    def h_cross3(v: str, p: ProjectProfile) -> list[str]:
        p.has_digital_component = v == "A"
        return []

    def h_cross4(v: str, p: ProjectProfile) -> list[str]:
        p.has_field_observation = v == "A"
        return []

    def h_cross5(v: str, p: ProjectProfile) -> list[str]:
        p.needs_internal_approval = v == "A"
        return []

    def h_cross6(v: str, p: ProjectProfile) -> list[str]:
        p.has_associated_drug = v in ("A", "B")
        if v in ("A", "B"):
            p.add_uncertainty("clinical_evidence")
            p.add_uncertainty("regulatory")
        elif v == "D":
            p.add_uncertainty("regulatory")
        return []

    def h_final(v: str, p: ProjectProfile) -> list[str]:
        p.timeline = {"A": "short", "B": "medium", "C": "long"}[v]
        return []

    return {
        "Q01": Question("Q01",
            text="Qual é a origem deste projeto?",
            options={
                "A": "Demanda interna (estratégia da empresa)",
                "B": "Demanda de cliente / parceiro externo",
                "C": "Oportunidade identificada no mercado",
                "D": "Necessidade clínica não atendida observada em campo",
            },
            handler=h_origin),

        "Q02": Question("Q02",
            text="Qual é a estratégia de desenvolvimento deste produto?",
            options={
                "A": "OEM puro — comprar pronto e revender",
                "B": "White label / marca própria sobre produto externo",
                "C": "Adaptação documental (IFU, rótulo, embalagem)",
                "D": "Adaptação técnica (design, ergonomia, indicação)",
                "E": "Alteração de material do produto",
                "F": "Substituição de fornecedor de produto atual",
                "G": "Nacionalização (substituição de componente importado)",
                "H": "Internalização produtiva (passar a fabricar internamente)",
                "I": "Novo kit médico",
                "J": "Novo acessório para produto existente",
                "K": "Produto similar a concorrente (me-too)",
                "L": "Inovação incremental — melhoria significativa",
                "M": "Inovação radical — produto novo sem precedente",
                "N": "Plataforma tecnológica / família de produtos",
            },
            handler=h_strategy,
            multiple=True,
            help_text="Selecione todas as estratégias que se aplicam ao caso."),

        "Q03": Question("Q03",
            text="Qual responsabilidade a empresa assumirá com este produto?",
            options={
                "A": "Titular da marca",
                "B": "Titular do registro / notificação regulatória",
                "C": "Responsável técnico pelo produto",
                "D": "Fabricante",
                "E": "Importador",
                "F": "Distribuidor",
            },
            handler=h_responsibility,
            multiple=True),

        "Q_USER1": Question("Q_USER1",
            text="Quem será o usuário principal do produto?",
            options={
                "A": "Médico / cirurgião",
                "B": "Enfermeiro / técnico de saúde",
                "C": "Paciente / cuidador",
                "D": "Equipe de produção / processamento interno",
                "E": "Hospital / clínica / comprador institucional",
                "F": "Múltiplos usuários principais",
            },
            handler=h_user1),

        "Q04": Question("Q04",
            text="O produto terá contato com o paciente?",
            options={
                "A": "Não — equipamento, software ou infraestrutura sem contato",
                "B": "Sim — contato externo (pele intacta)",
                "C": "Sim — contato com mucosas ou orifícios naturais",
                "D": "Sim — invasivo temporário (cirurgia, cateter, agulha)",
                "E": "Sim — implantável ou de longa permanência",
            },
            handler=h_patient_contact),

        "Q05": Question("Q05",
            text="O produto necessitará ser estéril?",
            options={
                "A": "Sim — produto estéril confirmado",
                "B": "Não",
                "C": "Não sei ainda — esterilidade indefinida",
            },
            handler=h_sterility),

        "Q_REG1": Question("Q_REG1",
            text="A classificação regulatória do produto já foi identificada?",
            options={
                "A": "Sim — classe e agência confirmadas (ANVISA, FDA, CE)",
                "B": "Temos ideia, mas não confirmado",
                "C": "Não — classificação desconhecida",
            },
            handler=h_reg1),

        "Q_REG2": Question("Q_REG2",
            text="Existe registro ou notificação similar já ativo no mercado?",
            options={
                "A": "Sim — já identificado",
                "B": "Não",
                "C": "Não sei",
            },
            handler=h_reg2),

        "Q_REG3": Question("Q_REG3",
            text="As normas técnicas aplicáveis ao produto já foram identificadas?",
            options={
                "A": "Sim",
                "B": "Parcialmente",
                "C": "Não",
            },
            handler=h_reg3),

        "Q_OEM1": Question("Q_OEM1",
            text="[OEM] Situação atual do fornecedor externo:",
            options={
                "A": "Fornecedor único já identificado e em negociação",
                "B": "Fornecedor ainda não definido — em prospecção",
                "C": "Múltiplos fornecedores em avaliação simultânea",
            },
            handler=h_oem1),

        "Q_OEM2": Question("Q_OEM2",
            text="[OEM] Quais customizações serão necessárias?",
            options={
                "A": "Rotulagem / idioma / marca",
                "B": "IFU (Instruções de Uso)",
                "C": "Embalagem",
                "D": "Nenhuma — produto usado como recebido",
            },
            handler=h_oem2,
            multiple=True,
            exclusive_options={"D"}),

        "Q_OEM3": Question("Q_OEM3",
            text="[OEM] O custo unitário é fator crítico de decisão?",
            options={
                "A": "Sim — custo é decisivo para viabilidade",
                "B": "Sim — custo importa, mas não é único critério",
                "C": "Não — outros fatores são prioritários",
            },
            handler=h_oem3),

        "Q_SUP1": Question("Q_SUP1",
            text="[Substituição de Fornecedor] Como está a situação do fornecedor alternativo?",
            options={
                "A": "Alternativo já identificado e em avaliação",
                "B": "Alternativo ainda em prospecção",
                "C": "Múltiplos alternativos sendo avaliados",
            },
            handler=h_sup1),

        "Q_ADP1": Question("Q_ADP1",
            text="[Adaptação] O que será modificado?",
            options={
                "A": "Ergonomia / design / interface",
                "B": "Indicação clínica / uso pretendido",
                "C": "Material / composição",
                "D": "Embalagem",
                "E": "Rotulagem / IFU",
                "F": "Processo produtivo",
            },
            handler=h_adp1,
            multiple=True),

        "Q_ADP2": Question("Q_ADP2",
            text="[Adaptação] Existe produto de referência para esta adaptação?",
            options={
                "A": "Sim — produto de concorrente",
                "B": "Sim — produto próprio atual",
                "C": "Não — adaptação sem referência direta",
            },
            handler=h_adp2),

        "Q_KIT1": Question("Q_KIT1",
            text="[Kit / Acessório] Características do kit ou acessório:",
            options={
                "A": "Agrupa produtos de fornecedores diferentes",
                "B": "Pelo menos um componente é estéril",
                "C": "Embalagem será desenvolvida especificamente para o kit",
                "D": "IFU específica será necessária",
                "E": "Acessório deve ser compatível com produto já registrado",
            },
            handler=h_kit1,
            multiple=True),

        "Q_SIM1": Question("Q_SIM1",
            text="[Produto Similar] O produto de referência do concorrente está disponível para análise?",
            options={
                "A": "Sim — temos acesso ao produto",
                "B": "Acesso parcial — apenas especificações/literatura",
                "C": "Não — apenas informações públicas disponíveis",
            },
            handler=h_sim1),

        "Q_INT1": Question("Q_INT1",
            text="[Internalização] Qual o escopo da produção interna prevista?",
            options={
                "A": "Apenas montagem final",
                "B": "Fabricação de componentes principais",
                "C": "Produção integral (tooling, embalagem, esterilização)",
                "D": "Ainda não definido",
            },
            handler=h_int1),

        "Q_INN1": Question("Q_INN1",
            text="[Inovação] Nível de maturidade da tecnologia central:",
            options={
                "A": "Consolidada — dominada internamente",
                "B": "Existente — nova para nossa empresa",
                "C": "Emergente — ainda em desenvolvimento no mercado",
                "D": "Inédita — sem precedente",
            },
            handler=h_inn1),

        "Q_INN2": Question("Q_INN2",
            text="[Inovação] Principais incertezas abertas:",
            options={
                "A": "Evidência clínica — não sabemos se funcionará clinicamente",
                "B": "Espaço de IP — pode haver patentes bloqueando",
                "C": "Tecnologia — viabilidade técnica incerta",
                "D": "Fornecedor — componentes-chave sem fonte definida",
                "E": "Regulatório — classificação ou caminho desconhecido",
                "F": "Custo — viabilidade econômica indefinida",
                "G": "Manufatura — processo produtivo não definido",
            },
            handler=h_inn2,
            multiple=True),

        "Q_CROSS1": Question("Q_CROSS1",
            text="Qual o nível de clareza do problema clínico que o produto resolve?",
            options={
                "A": "Claro e bem documentado",
                "B": "Parcialmente definido",
                "C": "Vago — ainda em entendimento",
            },
            handler=h_cross1),

        "Q_CROSS2": Question("Q_CROSS2",
            text="O projeto envolve múltiplos perfis de usuário ou stakeholders?",
            options={
                "A": "Sim — médicos, pacientes, técnicos, gestores etc.",
                "B": "Não — usuário único e bem definido",
            },
            handler=h_cross2),

        "Q_CROSS3": Question("Q_CROSS3",
            text="O produto terá componente digital (software, app, IoT, IA)?",
            options={"A": "Sim", "B": "Não"},
            handler=h_cross3),

        "Q_CROSS4": Question("Q_CROSS4",
            text="Já foi realizada observação em campo ou visita a usuários reais?",
            options={"A": "Sim", "B": "Não"},
            handler=h_cross4),

        "Q_CROSS5": Question("Q_CROSS5",
            text="O conceito precisará de aprovação formal de comitê interno?",
            options={"A": "Sim", "B": "Não"},
            handler=h_cross5),

        "Q_CROSS6": Question("Q_CROSS6",
            text="O produto terá interação, condução ou uso associado a medicamento, fluido, substância química ou solução clínica?",
            options={
                "A": "Sim — medicamento ou substância ativa",
                "B": "Sim — fluido ou solução clínica sem ação medicamentosa principal",
                "C": "Não",
                "D": "Não sei ainda",
            },
            handler=h_cross6),

        "Q_FINAL": Question("Q_FINAL",
            text="Horizonte de tempo esperado para aprovação do conceito:",
            options={
                "A": "Curto prazo — até 3 meses",
                "B": "Médio prazo — 3 a 6 meses",
                "C": "Longo prazo — mais de 6 meses",
            },
            handler=h_final),
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
        self.finished: bool = False

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
        question = self.get_current_question()
        if question is None:
            self.finished = True
            self.profile.compute_complexity()
            return

        qid = question.id
        if question.multiple:
            if not isinstance(value, list):
                value = [str(value)]
            selected = [str(v) for v in value]
            if not selected:
                raise ValueError("Selecione pelo menos uma opção.")

            if question.exclusive_options:
                overlap = set(selected) & question.exclusive_options
                if overlap and len(selected) > 1:
                    labels = ", ".join(question.options[o] for o in overlap)
                    raise ValueError(f"A opção '{labels}' não pode ser combinada com outras opções.")

            labels = [question.options[v] for v in selected]
            self.profile.raw_answers.append({"q": qid, "value": selected, "label": labels})
            next_ids = question.handler(selected, self.profile)
        else:
            if not isinstance(value, str):
                raise ValueError("Resposta inválida.")
            if value not in question.options:
                raise ValueError("Resposta inválida.")
            self.profile.raw_answers.append({"q": qid, "value": value, "label": question.options[value]})
            next_ids = question.handler(value, self.profile)

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
        total_dynamic = len(self.answered) + len([qid for qid in self.queue if qid not in self.answered])
        answered = len(self.answered)
        ratio = 1.0 if total_dynamic == 0 else answered / total_dynamic
        return answered, total_dynamic, ratio

    def apply_rules(self) -> list[SelectedTool]:
        p = self.profile
        p.compute_complexity()

        result: list[SelectedTool] = []
        seen: set[str] = set()

        for rule in RULES:
            if rule.tool_id in seen or rule.tool_id not in TOOL_LIBRARY:
                continue
            try:
                if rule.condition(p):
                    selected = SelectedTool(
                        tool=TOOL_LIBRARY[rule.tool_id],
                        priority=rule.priority_fn(p),
                        reason=rule.reason_fn(p),
                    )
                    result.append(selected)
                    seen.add(rule.tool_id)
            except Exception as e:
                raise RuntimeError(
                    f"[ERRO] Falha ao aplicar regra da ferramenta '{rule.tool_id}': {e}"
                ) from e

        order = {
            ToolPriority.MANDATORY: 0,
            ToolPriority.RECOMMENDED: 1,
            ToolPriority.OPTIONAL: 2,
        }
        result.sort(key=lambda s: (order[s.priority], s.tool.category.value, s.tool.id))
        return result

    def selected_as_groups(self, selected: list[SelectedTool]) -> dict[ToolPriority, list[SelectedTool]]:
        grouped = {
            ToolPriority.MANDATORY: [],
            ToolPriority.RECOMMENDED: [],
            ToolPriority.OPTIONAL: [],
        }
        for s in selected:
            grouped[s.priority].append(s)
        return grouped

    def generate_report(self, selected: list[SelectedTool] | None = None) -> str:
        if selected is None:
            selected = self.apply_rules()

        p = self.profile
        p.compute_complexity()
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        w = 88

        lines: list[str] = []

        def sep(c: str = "=") -> None:
            lines.append(c * w)

        def h1(title: str) -> None:
            sep("=")
            lines.append(f"  {title}")
            sep("=")

        def h2(title: str) -> None:
            sep("─")
            lines.append(f"  {title}")
            sep("─")

        def row(k: str, v: Any) -> None:
            lines.append(f"  {k:<42} {v}")

        h1("MED CONCEPT ENGINE — CONCEPT REPORT")
        lines.append(f"  Gerado em : {now}")
        lines.append("  Versão    : Aplicativo Streamlit — Motor por Regras")

        h2("PERFIL MULTICAMADAS DO PROJETO")
        row("Estratégias de Desenvolvimento:", ", ".join(p.development_strategy) or "—")
        row("Responsabilidade da Empresa:", ", ".join(p.company_responsibility) or "—")
        row("Origem do Projeto:", p.project_origin or "—")
        row("Usuário Principal:", p.user_type or "—")
        row("Contato com Paciente:", "Sim" if p.has_patient_contact else "Não")
        row("Invasividade:", f"{p.invasiveness_level}/4")
        row("Esterilidade Necessária:", "Sim" if p.sterility_required else "Não")
        row("Esterilidade Indefinida:", "Sim" if p.sterility_unknown else "Não")
        row("Componente Digital:", "Sim" if p.has_digital_component else "Não")
        row("Medicamento/Fluido Associado:", "Sim" if p.has_associated_drug else "Não")
        row("Multi-stakeholder:", "Sim" if p.multi_stakeholder else "Não")
        row("Maturidade Tecnológica:", f"{p.tech_maturity}/3")
        row("Incerteza Regulatória:", p.regulatory_uncertainty or "—")
        row("Classe Regulatória Definida:", "Sim" if p.has_regulatory_class else "Não")
        row("Registro Similar Existe:", "Sim" if p.has_similar_registration else "Não")
        row("Produto de Referência Existe:", "Sim" if p.has_existing_reference else "Não")
        row("Fornecedor Externo:", "Sim" if p.has_external_supplier() else "Não")
        row("Custo Crítico:", "Sim" if p.cost_is_critical else "Não")
        row("Aprovação Interna Necessária:", "Sim" if p.needs_internal_approval else "Não")
        row("Incertezas de Conceito:", ", ".join(p.concept_uncertainties) or "nenhuma identificada")
        row("Clareza do Problema:", f"{p.problem_clarity}/2")

        h2(f"SCORE DE COMPLEXIDADE: {p.complexity.name} ({p.complexity_score} pts)")
        for factor, pts in sorted(p.score_breakdown.items(), key=lambda x: -x[1]):
            bar = "█" * pts if pts > 0 else "·"
            lines.append(f"  {factor:<42} {pts:2d} pts  {bar}")

        grouped = self.selected_as_groups(selected)
        h2(f"FERRAMENTAS RECOMENDADAS — {len(selected)} no total")
        lines.append(f"  ✅ Obrigatórias : {len(grouped[ToolPriority.MANDATORY])}")
        lines.append(f"  🔵 Recomendadas : {len(grouped[ToolPriority.RECOMMENDED])}")
        lines.append(f"  ⚪ Opcionais    : {len(grouped[ToolPriority.OPTIONAL])}")

        for priority in [ToolPriority.MANDATORY, ToolPriority.RECOMMENDED, ToolPriority.OPTIONAL]:
            group = grouped[priority]
            if not group:
                continue

            label = priority.value.upper()
            lines.append("")
            lines.append(f"  {label}")
            lines.append("  " + "·" * (w - 2))

            by_cat: dict[ToolCategory, list[SelectedTool]] = {}
            for s in group:
                by_cat.setdefault(s.tool.category, []).append(s)

            for cat, items in by_cat.items():
                lines.append("")
                lines.append(f"    📂 {cat.value}")
                for s in items:
                    lines.append("")
                    lines.append(f"      [{s.tool.id}] {s.tool.name}")
                    desc = textwrap.fill(s.tool.description, width=w - 12, subsequent_indent=" " * 12)
                    reason = textwrap.fill(f"↳ {s.reason}", width=w - 12, subsequent_indent=" " * 14)
                    lines.append(f"          📋 {desc}")
                    lines.append(f"          {reason}")

        h2("PRÓXIMOS PASSOS — ENTREGA AO TIME DE PROJETO")
        steps = [
            "1. Conduzir todas as ferramentas obrigatórias listadas acima.",
            "2. Avaliar ferramentas recomendadas conforme tempo, prioridade e recursos disponíveis.",
            "3. Consolidar evidências no Relatório de Conceito (OUT02).",
            "4. Realizar Gate de Conceito (CON02) com stakeholders.",
            "5. Assinar Termo de Conceito Aprovado (OUT06), quando aplicável.",
            "6. Montar Pacote de Transferência para o time de Projeto (OUT07).",
        ]
        for s in steps:
            lines.append(f"  {s}")

        sep("=")
        lines.append("  Fim do Relatório — Med Concept Engine")
        sep("=")
        return "\n".join(lines)

    def export_json(self, selected: list[SelectedTool] | None = None) -> dict[str, Any]:
        if selected is None:
            selected = self.apply_rules()

        p = self.profile
        p.compute_complexity()

        return {
            "generated_at": datetime.now().isoformat(),
            "engine_version": "v4-streamlit-rule-based",
            "project_profile": {
                "development_strategy": p.development_strategy,
                "company_responsibility": p.company_responsibility,
                "project_origin": p.project_origin,
                "user_type": p.user_type,
                "has_patient_contact": p.has_patient_contact,
                "invasiveness_level": p.invasiveness_level,
                "sterility_required": p.sterility_required,
                "sterility_unknown": p.sterility_unknown,
                "has_digital_component": p.has_digital_component,
                "has_associated_drug": p.has_associated_drug,
                "multi_stakeholder": p.multi_stakeholder,
                "tech_maturity": p.tech_maturity,
                "regulatory_uncertainty": p.regulatory_uncertainty,
                "has_regulatory_class": p.has_regulatory_class,
                "has_similar_registration": p.has_similar_registration,
                "has_existing_reference": p.has_existing_reference,
                "supplier_dependency": p.supplier_dependency,
                "cost_is_critical": p.cost_is_critical,
                "concept_uncertainties": p.concept_uncertainties,
                "complexity": p.complexity.name,
                "complexity_score": p.complexity_score,
                "score_breakdown": p.score_breakdown,
            },
            "tools": [
                {
                    "id": s.tool.id,
                    "name": s.tool.name,
                    "category": s.tool.category.value,
                    "priority": s.priority.name,
                    "priority_label": s.priority.value,
                    "description": s.tool.description,
                    "reason": s.reason,
                }
                for s in selected
            ],
            "answers": p.raw_answers,
        }

    def export_json_string(self, selected: list[SelectedTool] | None = None) -> str:
        return json.dumps(self.export_json(selected), ensure_ascii=False, indent=2)
