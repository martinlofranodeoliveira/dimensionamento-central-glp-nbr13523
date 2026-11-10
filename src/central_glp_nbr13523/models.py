"""Modelos de dados e enumerações tipadas para Centrais de GLP (NBR 13523:2019).

Todos os campos utilizam frações racionais exatas (`Fraction`) e inteiros,
sem ponto flutuante IEEE-754.
"""

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import List


class TipoRecipiente(str, Enum):
    """Tipos padronizados de recipientes para GLP conforme NBR 13523."""
    P_13 = "P_13"
    P_20 = "P_20"
    P_45 = "P_45"
    P_90 = "P_90"
    P_190 = "P_190"
    E_500 = "E_500"
    E_1000 = "E_1000"
    E_2000 = "E_2000"
    E_4000 = "E_4000"


class ClasseCentral(str, Enum):
    """Classes regulamentares de central de GLP por volume total (Tabela 1/2)."""
    CLASSE_I = "CLASSE_I"
    CLASSE_II = "CLASSE_II"
    CLASSE_III = "CLASSE_III"
    CLASSE_IV = "CLASSE_IV"
    CLASSE_V = "CLASSE_V"
    CLASSE_VI = "CLASSE_VI"


class TipoConsumidor(str, Enum):
    """Classificação do estabelecimento consumidor de GLP."""
    RESIDENCIAL_COLETIVO = "RESIDENCIAL_COLETIVO"
    COMERCIAL_RESTAURANTE = "COMERCIAL_RESTAURANTE"
    INDUSTRIAL = "INDUSTRIAL"
    HOSPITALAR = "HOSPITALAR"
    HOTELARIA = "HOTELARIA"


class TipoRegulagemPressao(str, Enum):
    """Estágio de regulagem e pressão nominal de serviço."""
    BAIXA_PRESSAO_2_8_KPA = "BAIXA_PRESSAO_2_8_KPA"
    MEDIA_PRESSAO_50_KPA = "MEDIA_PRESSAO_50_KPA"


@dataclass(frozen=True)
class DadosMuroProtecao:
    """Configuração de parede cega corta-fogo para redução de distâncias."""
    possui_muro: bool
    altura_m: Fraction = Fraction(0, 1)
    trrf_min: int = 0
    distancia_pelo_contorno_m: Fraction = Fraction(0, 1)


@dataclass(frozen=True)
class DadosAfastamentosReais:
    """Distâncias reais medidas no projeto da central (em metros)."""
    distancia_aberturas_m: Fraction
    distancia_divisa_lote_m: Fraction
    distancia_fontes_ignicao_m: Fraction
    distancia_ralos_depressoes_m: Fraction
    distancia_tanques_inflamaveis_m: Fraction = Fraction(999, 1)


@dataclass(frozen=True)
class DadosEquipamentoConsumo:
    """Equipamento consumidor de GLP para estimativa de vazão."""
    id: str
    descricao: str
    consumo_kg_h: Fraction
    fator_simultaneidade: Fraction = Fraction(1, 1)


@dataclass(frozen=True)
class DadosCentralGLP:
    """Conjunto de dados de entrada para dimensionamento da Central de GLP."""
    identificacao_projeto: str
    tipo_consumidor: TipoConsumidor
    tipo_recipiente: TipoRecipiente
    recipientes_em_servico: int
    recipientes_em_reserva: int
    consumo_pico_kg_h: Fraction
    afastamentos: DadosAfastamentosReais
    muro_protecao: DadosMuroProtecao = DadosMuroProtecao(possui_muro=False)
    tipo_regulagem: TipoRegulagemPressao = TipoRegulagemPressao.BAIXA_PRESSAO_2_8_KPA
    responsavel_tecnico: str = ""
    equipamentos: List[DadosEquipamentoConsumo] = field(default_factory=list)


@dataclass(frozen=True)
class ResultadoItemAfastamento:
    """Auditoria de um afastamento de segurança específico."""
    item: str
    distancia_exigida_m: Fraction
    distancia_real_m: Fraction
    conforme: bool
    observacao: str


@dataclass(frozen=True)
class ResultadoVaporizacao:
    """Auditoria da taxa de vaporização natural versus consumo."""
    consumo_pico_kg_h: Fraction
    taxa_vaporizacao_por_recipiente_kg_h: Fraction
    recipientes_servico_minimos_requeridos: int
    recipientes_servico_especificados: int
    capacidade_vaporizacao_total_kg_h: Fraction
    vaporizacao_atende: bool
    necessita_vaporizador_artificial: bool


@dataclass(frozen=True)
class ResultadoCentralGLP:
    """Relatório consolidado de dimensionamento e auditoria da Central de GLP."""
    identificacao_projeto: str
    tipo_consumidor: TipoConsumidor
    tipo_recipiente: TipoRecipiente
    classe_central: ClasseCentral
    volume_total_m3: Fraction
    capacidade_massa_total_kg: int
    total_recipientes: int
    configuracao_bateria: str
    resultado_vaporizacao: ResultadoVaporizacao
    capacidade_minima_regulador_1_estagio_kg_h: Fraction
    pressao_saida_1_estagio_bar: Fraction
    pressao_servico_kpa: Fraction
    extintores_minimos_qtd: int
    extintores_capacidade_min: str
    exige_resfriamento_agua: bool
    auditoria_afastamentos: List[ResultadoItemAfastamento]
    conformidade_afastamentos: bool
    conformidade_geral: bool
    alertas_tecnicos: List[str]
