"""Módulo raiz de dimensionamento de Centrais de GLP (ABNT NBR 13523:2019).

Desenvolvido pela Lofrano Tecnologia com Zero-Float inegociável.
"""

from central_glp_nbr13523.calculator import (
    auditar_afastamentos,
    auditar_vaporizacao,
    calcular_consumo_efetivo,
    calcular_volume_e_massa_total,
    classificar_classe_central,
    dimensionar_central_glp,
)
from central_glp_nbr13523.codecs import (
    carregar_central_glp_json,
    exportar_resultado_json,
)
from central_glp_nbr13523.constants import (
    CATALOGO_RECIPIENTES,
    LIMITES_CLASSE_VOLUME_M3,
    TABELA_AFASTAMENTOS,
)
from central_glp_nbr13523.exporters import (
    gerar_csv_afastamentos,
    gerar_pacote_zip_central_glp,
    gerar_relatorio_central_glp_texto,
)
from central_glp_nbr13523.models import (
    ClasseCentral,
    DadosAfastamentosReais,
    DadosCentralGLP,
    DadosEquipamentoConsumo,
    DadosMuroProtecao,
    ResultadoCentralGLP,
    ResultadoItemAfastamento,
    ResultadoVaporizacao,
    TipoConsumidor,
    TipoRecipiente,
    TipoRegulagemPressao,
)
from central_glp_nbr13523.svg_generator import gerar_painel_svg

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "auditar_afastamentos",
    "auditar_vaporizacao",
    "calcular_consumo_efetivo",
    "calcular_volume_e_massa_total",
    "classificar_classe_central",
    "dimensionar_central_glp",
    "carregar_central_glp_json",
    "exportar_resultado_json",
    "gerar_csv_afastamentos",
    "gerar_pacote_zip_central_glp",
    "gerar_relatorio_central_glp_texto",
    "gerar_painel_svg",
    "ClasseCentral",
    "DadosAfastamentosReais",
    "DadosCentralGLP",
    "DadosEquipamentoConsumo",
    "DadosMuroProtecao",
    "ResultadoCentralGLP",
    "ResultadoItemAfastamento",
    "ResultadoVaporizacao",
    "TipoConsumidor",
    "TipoRecipiente",
    "TipoRegulagemPressao",
    "CATALOGO_RECIPIENTES",
    "LIMITES_CLASSE_VOLUME_M3",
    "TABELA_AFASTAMENTOS",
]
