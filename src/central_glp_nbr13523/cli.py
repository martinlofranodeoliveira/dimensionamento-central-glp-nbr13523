"""Interface de Linha de Comando (CLI) para dimensionamento de Centrais de GLP NBR 13523:2019."""

import argparse
import sys
from typing import Sequence

from central_glp_nbr13523 import __version__
from central_glp_nbr13523.calculator import dimensionar_central_glp
from central_glp_nbr13523.codecs import carregar_central_glp_json, exportar_resultado_json
from central_glp_nbr13523.exporters import (
    gerar_csv_afastamentos,
    gerar_pacote_zip_central_glp,
    gerar_relatorio_central_glp_texto,
)
from central_glp_nbr13523.svg_generator import gerar_painel_svg


def _comando_calcular(args: argparse.Namespace) -> int:
    try:
        with open(args.arquivo, "r", encoding="utf-8") as f:
            conteudo = f.read()
    except Exception as err:
        print(f"Erro ao ler arquivo de entrada: {err}", file=sys.stderr)
        return 1

    try:
        dados = carregar_central_glp_json(conteudo)
    except Exception as err:
        print(f"Erro ao processar JSON: {err}", file=sys.stderr)
        return 1

    resultado = dimensionar_central_glp(dados)

    # Geração do pacote ZIP determinístico se solicitado
    if args.pacote_zip:
        try:
            svg_conteudo = gerar_painel_svg(resultado)
            gerar_pacote_zip_central_glp(resultado, args.pacote_zip, svg_conteudo)
            print(f"[ZIP] Pacote determinístico gerado com sucesso em '{args.pacote_zip}'")
        except Exception as err:
            print(f"Erro ao gerar pacote ZIP: {err}", file=sys.stderr)
            return 1

    # Formatação da saída solicitada
    formato = args.formato.lower()
    if formato == "json":
        saida_str = exportar_resultado_json(resultado)
    elif formato == "csv":
        saida_str = gerar_csv_afastamentos(resultado)
    elif formato == "svg":
        saida_str = gerar_painel_svg(resultado)
    else:
        saida_str = gerar_relatorio_central_glp_texto(resultado)

    if args.saida:
        try:
            with open(args.saida, "w", encoding="utf-8") as f:
                f.write(saida_str)
            print(f"[OK] Saída ({formato}) salva com sucesso em '{args.saida}'")
        except Exception as err:
            print(f"Erro ao salvar arquivo de saída: {err}", file=sys.stderr)
            return 1
    else:
        print(saida_str)

    return 0


def _comando_catalogo(args: argparse.Namespace) -> int:
    print("=" * 84)
    print("     LOFRANO TECNOLOGIA - PARÂMETROS NORMATIVOS DA ABNT NBR 13523:2019")
    print("     Central de Gás Liquefeito de Petróleo (GLP) - Projeto e Segurança")
    print("=" * 84)
    print("1. RECIPIENTES PADRONIZADOS E TAXAS DE VAPORIZAÇÃO NATURAL (20°C)")
    print("  - P-13  : 13 kg  (0,031 m³)  | Vap: 0,35 kg/h | Residencial Individual")
    print("  - P-20  : 20 kg  (0,048 m³)  | Vap: 0,50 kg/h | Empilhadeiras e Uso Especial")
    print("  - P-45  : 45 kg  (0,108 m³)  | Vap: 1,00 kg/h | Baterias Prediais / Comerciais")
    print("  - P-90  : 90 kg  (0,216 m³)  | Vap: 2,00 kg/h | Comercial / Cozinhas")
    print("  - P-190 : 190 kg (0,456 m³)  | Vap: 3,50 kg/h | Comercial / Industrial")
    print("  - E-500 : 500 kg (1,200 m³)  | Vap: 12,0 kg/h | Tanque Estacionário")
    print("  - E-1000: 1000 kg (2,400 m³) | Vap: 20,0 kg/h | Tanque Estacionário")
    print("  - E-2000: 2000 kg (4,800 m³) | Vap: 35,0 kg/h | Tanque Estacionário")
    print("  - E-4000: 4000 kg (9,600 m³) | Vap: 60,0 kg/h | Tanque Estacionário")
    print("-" * 84)
    print("2. CLASSIFICAÇÃO DA CENTRAL POR VOLUME TOTAL (TABELA 1 E 2 DA NBR 13523)")
    print("  - Classe I   : V <= 0,54 m³       (até 225 kg de GLP)")
    print("  - Classe II  : 0,54 < V <= 2,16 m³ (226 kg a 900 kg)")
    print("  - Classe III : 2,16 < V <= 5,40 m³ (901 kg a 2.250 kg)")
    print("  - Classe IV  : 5,40 < V <= 16,20 m³ (2.251 kg a 6.750 kg)")
    print("  - Classe V   : 16,20 < V <= 32,40 m³ (6.751 kg a 13.500 kg)")
    print("  - Classe VI  : 32,40 < V <= 64,80 m³ (13.501 kg a 27.000 kg)")
    print("-" * 84)
    print("3. AFASTAMENTOS MÍNIMOS DE SEGURANÇA POR CLASSE (METROS)")
    print("  Classe     Aberturas  Divisas  Fontes Ignição  Ralos/Depressões  Tanques Inflam.")
    print("  Classe I     1,5 m     1,5 m       3,0 m            1,5 m             6,0 m")
    print("  Classe II    3,0 m     3,0 m       3,0 m            1,5 m             6,0 m")
    print("  Classe III   6,0 m     6,0 m       6,0 m            3,0 m            10,0 m")
    print("  Classe IV    7,5 m     7,5 m       7,5 m            3,0 m            10,0 m")
    print("  Classe V    10,0 m    10,0 m      10,0 m            3,0 m            15,0 m")
    print("  Classe VI   15,0 m    15,0 m      15,0 m            3,0 m            15,0 m")
    print("-" * 84)
    print("4. COMPENSAÇÃO POR MURO CORTA-FOGO (NBR 13523 ITEM 5.3)")
    print("  - Altura mínima: 1,80 m")
    print("  - Resistência ao fogo mínima: TRRF 120 minutos (parede cega sem aberturas)")
    print("  - Redução de distância direta para 0 m permitida se a distância contornando o")
    print("    muro (distância pelo contorno) for maior ou igual ao afastamento exigido.")
    print("=" * 84)
    return 0


def _comando_gerar_exemplo(args: argparse.Namespace) -> int:
    exemplo_json = """{
  "identificacao_projeto": "Edifício Residencial Jardins Prime",
  "tipo_consumidor": "RESIDENCIAL_COLETIVO",
  "tipo_recipiente": "P_45",
  "recipientes_em_servico": 6,
  "recipientes_em_reserva": 6,
  "consumo_pico_kg_h": "5.5",
  "tipo_regulagem": "BAIXA_PRESSAO_2_8_KPA",
  "responsavel_tecnico": "Eng. Martin Lofrano de Oliveira - CREA/SP",
  "afastamentos": {
    "distancia_aberturas_m": "3.5",
    "distancia_divisa_lote_m": "3.0",
    "distancia_fontes_ignicao_m": "4.0",
    "distancia_ralos_depressoes_m": "2.0",
    "distancia_tanques_inflamaveis_m": "10.0"
  },
  "muro_protecao": {
    "possui_muro": false,
    "altura_m": "0",
    "trrf_min": 0,
    "distancia_pelo_contorno_m": "0"
  },
  "equipamentos": [
    {
      "id": "FOG-01",
      "descricao": "Fogões e Fornos a Gás (24 apartamentos)",
      "consumo_kg_h": "6",
      "fator_simultaneidade": "0.8"
    }
  ]
}
"""
    if args.saida:
        try:
            with open(args.saida, "w", encoding="utf-8") as f:
                f.write(exemplo_json)
            print(f"[OK] Modelo de exemplo gravado em '{args.saida}'")
        except Exception as err:
            print(f"Erro ao salvar arquivo de exemplo: {err}", file=sys.stderr)
            return 1
    else:
        print(exemplo_json)

    return 0


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser com suporte a flags em português."""
    parser = argparse.ArgumentParser(
        prog="central-glp-nbr13523",
        description="Dimensionamento e Auditoria de Centrais de GLP (ABNT NBR 13523:2019) - Lofrano Tecnologia",
        add_help=False,
    )

    parser.add_argument(
        "-h", "--help", "--ajuda",
        action="help",
        help="Exibe esta mensagem de ajuda e encerra.",
    )
    parser.add_argument(
        "-v", "--version", "--versao",
        action="version",
        version=f"central-glp-nbr13523 {__version__}",
        help="Exibe a versão do programa.",
    )

    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponíveis")

    # Comando calcular
    p_calc = subparsers.add_parser(
        "calcular",
        help="Dimensiona e audita a central a partir de arquivo JSON",
        add_help=False,
    )
    p_calc.add_argument("-h", "--help", "--ajuda", action="help", help="Ajuda do comando calcular.")
    p_calc.add_argument("arquivo", help="Caminho do arquivo JSON do projeto")
    p_calc.add_argument(
        "-f", "--formato",
        choices=["texto", "json", "csv", "svg"],
        default="texto",
        help="Formato do relatório de saída (padrão: texto)",
    )
    p_calc.add_argument("-o", "--saida", help="Arquivo de destino para a saída")
    p_calc.add_argument(
        "--pacote-zip",
        help="Gera pacote determinístico ZIP com memorial, JSON, CSV e SVG",
    )
    p_calc.set_defaults(func=_comando_calcular)

    # Comando catalogo
    p_cat = subparsers.add_parser(
        "catalogo",
        help="Exibe tabelas de recipientes, taxas de vaporização e afastamentos normativos",
        add_help=False,
    )
    p_cat.add_argument("-h", "--help", "--ajuda", action="help", help="Ajuda do catálogo.")
    p_cat.set_defaults(func=_comando_catalogo)

    # Comando gerar-exemplo
    p_ex = subparsers.add_parser(
        "gerar-exemplo",
        help="Emite modelo JSON canônico para preenchimento de projetos",
        add_help=False,
    )
    p_ex.add_argument("-h", "--help", "--ajuda", action="help", help="Ajuda do gerar-exemplo.")
    p_ex.add_argument("-o", "--saida", help="Arquivo de destino para o modelo JSON")
    p_ex.set_defaults(func=_comando_gerar_exemplo)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada principal da CLI."""
    parser = criar_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
