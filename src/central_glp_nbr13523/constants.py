"""Constantes e tabelas normativas da ABNT NBR 13523:2019 (Central de GLP).

Todas as grandezas dimensionais, volumétricas, térmicas e de segurança são
representadas rigorosamente em frações racionais (`fractions.Fraction`) e inteiros,
garantindo Zero-Float estrito.
"""

from fractions import Fraction
from typing import NamedTuple


class DadosCatalogoRecipiente(NamedTuple):
    """Parâmetros físicos e de vaporização padronizados por recipiente."""
    capacidade_massa_kg: int
    volume_m3: Fraction
    taxa_vaporizacao_natural_kg_h: Fraction
    eh_estacionario: bool
    descricao: str


# 1. Catálogo oficial de recipientes conforme NBR 13523:2019
CATALOGO_RECIPIENTES = {
    "P_13": DadosCatalogoRecipiente(
        capacidade_massa_kg=13,
        volume_m3=Fraction(31, 1000),  # 31 L = 0.031 m³
        taxa_vaporizacao_natural_kg_h=Fraction(7, 20),  # 0.35 kg/h
        eh_estacionario=False,
        descricao="Cilindro Transportável P-13 (13 kg / 31 L)",
    ),
    "P_20": DadosCatalogoRecipiente(
        capacidade_massa_kg=20,
        volume_m3=Fraction(48, 1000),  # 48 L = 0.048 m³
        taxa_vaporizacao_natural_kg_h=Fraction(1, 2),  # 0.50 kg/h
        eh_estacionario=False,
        descricao="Cilindro Transportável P-20 Industrial/Empilhadeira (20 kg / 48 L)",
    ),
    "P_45": DadosCatalogoRecipiente(
        capacidade_massa_kg=45,
        volume_m3=Fraction(108, 1000),  # 108 L = 0.108 m³
        taxa_vaporizacao_natural_kg_h=Fraction(1, 1),  # 1.00 kg/h
        eh_estacionario=False,
        descricao="Cilindro Transportável P-45 (45 kg / 108 L)",
    ),
    "P_90": DadosCatalogoRecipiente(
        capacidade_massa_kg=90,
        volume_m3=Fraction(216, 1000),  # 216 L = 0.216 m³
        taxa_vaporizacao_natural_kg_h=Fraction(2, 1),  # 2.00 kg/h
        eh_estacionario=False,
        descricao="Cilindro Transportável P-90 (90 kg / 216 L)",
    ),
    "P_190": DadosCatalogoRecipiente(
        capacidade_massa_kg=190,
        volume_m3=Fraction(456, 1000),  # 456 L = 0.456 m³
        taxa_vaporizacao_natural_kg_h=Fraction(7, 2),  # 3.50 kg/h
        eh_estacionario=False,
        descricao="Cilindro Transportável P-190 (190 kg / 456 L)",
    ),
    "E_500": DadosCatalogoRecipiente(
        capacidade_massa_kg=500,
        volume_m3=Fraction(12, 10),  # 1.2 m³ (1200 L)
        taxa_vaporizacao_natural_kg_h=Fraction(12, 1),  # 12.0 kg/h
        eh_estacionario=True,
        descricao="Tanque Estacionário E-500 (500 kg / 1.2 m³)",
    ),
    "E_1000": DadosCatalogoRecipiente(
        capacidade_massa_kg=1000,
        volume_m3=Fraction(24, 10),  # 2.4 m³ (2400 L)
        taxa_vaporizacao_natural_kg_h=Fraction(20, 1),  # 20.0 kg/h
        eh_estacionario=True,
        descricao="Tanque Estacionário E-1000 (1000 kg / 2.4 m³)",
    ),
    "E_2000": DadosCatalogoRecipiente(
        capacidade_massa_kg=2000,
        volume_m3=Fraction(48, 10),  # 4.8 m³ (4800 L)
        taxa_vaporizacao_natural_kg_h=Fraction(35, 1),  # 35.0 kg/h
        eh_estacionario=True,
        descricao="Tanque Estacionário E-2000 (2000 kg / 4.8 m³)",
    ),
    "E_4000": DadosCatalogoRecipiente(
        capacidade_massa_kg=4000,
        volume_m3=Fraction(96, 10),  # 9.6 m³ (9600 L)
        taxa_vaporizacao_natural_kg_h=Fraction(60, 1),  # 60.0 kg/h
        eh_estacionario=True,
        descricao="Tanque Estacionário E-4000 (4000 kg / 9.6 m³)",
    ),
}


# 2. Limites de volume total para classificação da Central de GLP (Tabela 1 e 2 da NBR 13523)
# Volume em m³
LIMITES_CLASSE_VOLUME_M3 = [
    ("CLASSE_I", Fraction(54, 100)),     # Até 0.54 m³
    ("CLASSE_II", Fraction(216, 100)),   # > 0.54 até 2.16 m³
    ("CLASSE_III", Fraction(540, 100)),  # > 2.16 até 5.40 m³
    ("CLASSE_IV", Fraction(1620, 100)),  # > 5.40 até 16.20 m³
    ("CLASSE_V", Fraction(3240, 100)),   # > 16.20 até 32.40 m³
    ("CLASSE_VI", Fraction(6480, 100)),  # > 32.40 até 64.80 m³
]


# 3. Matriz de Afastamentos Mínimos de Segurança (em metros - Fractions)
class AfastamentosClasse(NamedTuple):
    aberturas_edificacoes_m: Fraction
    divisa_lote_alinhamento_m: Fraction
    fontes_ignicao_m: Fraction
    ralos_depressoes_m: Fraction
    tanques_inflamaveis_m: Fraction
    extintores_minimos_qtd: int
    extintores_capacidade_min: str
    exige_resfriamento_agua: bool


TABELA_AFASTAMENTOS = {
    "CLASSE_I": AfastamentosClasse(
        aberturas_edificacoes_m=Fraction(3, 2),     # 1.5 m
        divisa_lote_alinhamento_m=Fraction(3, 2),   # 1.5 m
        fontes_ignicao_m=Fraction(3, 1),            # 3.0 m
        ralos_depressoes_m=Fraction(3, 2),          # 1.5 m
        tanques_inflamaveis_m=Fraction(6, 1),       # 6.0 m
        extintores_minimos_qtd=1,
        extintores_capacidade_min="20-B:C",
        exige_resfriamento_agua=False,
    ),
    "CLASSE_II": AfastamentosClasse(
        aberturas_edificacoes_m=Fraction(3, 1),     # 3.0 m
        divisa_lote_alinhamento_m=Fraction(3, 1),   # 3.0 m
        fontes_ignicao_m=Fraction(3, 1),            # 3.0 m
        ralos_depressoes_m=Fraction(3, 2),          # 1.5 m
        tanques_inflamaveis_m=Fraction(6, 1),       # 6.0 m
        extintores_minimos_qtd=2,
        extintores_capacidade_min="20-B:C",
        exige_resfriamento_agua=False,
    ),
    "CLASSE_III": AfastamentosClasse(
        aberturas_edificacoes_m=Fraction(6, 1),     # 6.0 m
        divisa_lote_alinhamento_m=Fraction(6, 1),   # 6.0 m
        fontes_ignicao_m=Fraction(6, 1),            # 6.0 m
        ralos_depressoes_m=Fraction(3, 1),          # 3.0 m
        tanques_inflamaveis_m=Fraction(10, 1),      # 10.0 m
        extintores_minimos_qtd=2,
        extintores_capacidade_min="40-B:C",
        exige_resfriamento_agua=False,
    ),
    "CLASSE_IV": AfastamentosClasse(
        aberturas_edificacoes_m=Fraction(15, 2),    # 7.5 m
        divisa_lote_alinhamento_m=Fraction(15, 2),  # 7.5 m
        fontes_ignicao_m=Fraction(15, 2),           # 7.5 m
        ralos_depressoes_m=Fraction(3, 1),          # 3.0 m
        tanques_inflamaveis_m=Fraction(10, 1),      # 10.0 m
        extintores_minimos_qtd=2,
        extintores_capacidade_min="80-B:C",
        exige_resfriamento_agua=True,
    ),
    "CLASSE_V": AfastamentosClasse(
        aberturas_edificacoes_m=Fraction(10, 1),    # 10.0 m
        divisa_lote_alinhamento_m=Fraction(10, 1),  # 10.0 m
        fontes_ignicao_m=Fraction(10, 1),           # 10.0 m
        ralos_depressoes_m=Fraction(3, 1),          # 3.0 m
        tanques_inflamaveis_m=Fraction(15, 1),      # 15.0 m
        extintores_minimos_qtd=3,
        extintores_capacidade_min="80-B:C",
        exige_resfriamento_agua=True,
    ),
    "CLASSE_VI": AfastamentosClasse(
        aberturas_edificacoes_m=Fraction(15, 1),    # 15.0 m
        divisa_lote_alinhamento_m=Fraction(15, 1),  # 15.0 m
        fontes_ignicao_m=Fraction(15, 1),           # 15.0 m
        ralos_depressoes_m=Fraction(3, 1),          # 3.0 m
        tanques_inflamaveis_m=Fraction(15, 1),      # 15.0 m
        extintores_minimos_qtd=3,
        extintores_capacidade_min="80-B:C",
        exige_resfriamento_agua=True,
    ),
}


# 4. Parâmetros de Regulagem e Engenharia de Tubulações
FATOR_SOBRECAPACIDADE_REGULADOR_1_ESTAGIO = Fraction(6, 5)  # 1.20 (20% de margem)
PRESSAO_SAIDA_1_ESTAGIO_BAR = Fraction(3, 2)               # 1.50 bar (150 kPa)
PRESSAO_BAIXA_SERVICO_KPA = Fraction(28, 10)               # 2.80 kPa (28 mbar)
PRESSAO_MEDIA_SERVICO_KPA = Fraction(50, 1)                # 50 kPa (0.5 bar)

ALTURA_MINIMA_MURO_PROTECAO_M = Fraction(9, 5)             # 1.80 m
TRRF_MINIMO_MURO_PROTECAO_MIN = 120                        # 120 minutos
