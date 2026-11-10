"""Exportadores técnicos: memorial descritivo, CSV sanitizado e ZIP determinístico.

Atende rigorosamente aos padrões de qualidade da Lofrano Tecnologia e ABNT NBR 13523:2019.
"""

import csv
import io
import os
import zipfile
from fractions import Fraction
from typing import Optional

from central_glp_nbr13523.codecs import exportar_resultado_json
from central_glp_nbr13523.models import ResultadoCentralGLP


def _fmt(val: Fraction, casas: int = 2) -> str:
    """Formata fração para string decimal com número fixo de casas sem ponto flutuante IEEE-754."""
    num = val.numerator
    den = val.denominator
    if den == 1:
        return f"{num}.0" if casas > 0 else str(num)
    inteiro = num // den
    resto = abs(num % den)
    fator = 10**casas
    frac_parte = (resto * fator + den // 2) // den
    return f"{inteiro}.{frac_parte:0{casas}d}"


def _sanitizar_campo_csv(val: str) -> str:
    """Sanitiza strings contra injeção de fórmulas de planilhas eletrônicas."""
    if val and val[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{val}"
    return val


def gerar_relatorio_central_glp_texto(res: ResultadoCentralGLP) -> str:
    """Gera memorial descritivo técnico detalhado para Central de GLP conforme NBR 13523."""
    linhas: list[str] = []
    w = 84
    linhas.append("=" * w)
    linhas.append("          LOFRANO TECNOLOGIA - ENGENHARIA DE INSTALAÇÕES DE GÁS E INCÊNDIO")
    linhas.append("            MEMORIAL DE DIMENSIONAMENTO DE CENTRAL DE GLP - NBR 13523:2019")
    linhas.append("=" * w)
    linhas.append(f"Projeto / Edificação:     {res.identificacao_projeto}")
    linhas.append(f"Tipo de Consumidor:       {res.tipo_consumidor.value}")
    linhas.append(f"Tipo de Recipiente:       {res.tipo_recipiente.value}")
    linhas.append(f"Configuração da Central:  {res.configuracao_bateria}")
    linhas.append(f"Volume Geométrico Total:  {_fmt(res.volume_total_m3, 3)} m³")
    linhas.append(f"Capacidade Nominal Massa: {res.capacidade_massa_total_kg} kg de GLP")
    linhas.append(f"Enquadramento Normativo:  {res.classe_central.value} (Tabela 1/2 da NBR 13523)")
    status_glo = "CONFORME" if res.conformidade_geral else "NÃO CONFORME / PENDÊNCIAS DETECTADAS"
    linhas.append(f"Status Geral do Projeto:  {status_glo}")
    linhas.append("-" * w)

    linhas.append("1. BALANÇO DE VAPORIZAÇÃO NATURAL VERSUS DEMANDA DE PICO")
    vap = res.resultado_vaporizacao
    linhas.append(f"  * Consumidor de Pico Informado:     {_fmt(vap.consumo_pico_kg_h, 2)} kg/h")
    linhas.append(f"  * Taxa de Vaporização por Unidade:  {_fmt(vap.taxa_vaporizacao_por_recipiente_kg_h, 2)} kg/h")
    linhas.append(f"  * Recipientes em Serviço Mínimos:   {vap.recipientes_servico_minimos_requeridos} un.")
    linhas.append(f"  * Recipientes em Serviço Adotados:  {vap.recipientes_servico_especificados} un.")
    linhas.append(f"  * Capacidade Vaporização Total:     {_fmt(vap.capacidade_vaporizacao_total_kg_h, 2)} kg/h")
    st_vap = "ATENDE AO CONSUMO" if vap.vaporizacao_atende else "VAPORIZAÇÃO INSUFICIENTE"
    linhas.append(f"  * Status da Vaporização Natural:    {st_vap}")
    if vap.necessita_vaporizador_artificial:
        linhas.append(
            "  * [EXIGÊNCIA] Necessária instalação de Vaporizador Artificial Forçado ou aumento da bateria."
        )
    linhas.append("-" * w)

    linhas.append("2. REGULAGEM DE PRESSÃO E DISTRIBUIÇÃO")
    linhas.append(
        f"  * Regulador de 1º Estágio (Capacidade Mínima): {_fmt(res.capacidade_minima_regulador_1_estagio_kg_h, 2)} kg/h"
    )
    linhas.append(f"  * Pressão de Saída do 1º Estágio:            {_fmt(res.pressao_saida_1_estagio_bar, 2)} bar")
    linhas.append(f"  * Pressão de Serviço Final (Rede Interna):   {_fmt(res.pressao_servico_kpa, 2)} kPa")
    linhas.append("-" * w)

    linhas.append("3. PROTEÇÃO E COMBATE A INCÊNDIO DA CENTRAL")
    linhas.append(
        f"  * Extintores Mínimos na Central: {res.extintores_minimos_qtd} unidade(s) de pó químico {res.extintores_capacidade_min}"
    )
    if res.exige_resfriamento_agua:
        linhas.append(
            "  * [ATENÇÃO] Exigido sistema de proteção por água (resfriamento por hidrantes ou nebulizadores) "
            "conforme IT do Corpo de Bombeiros para esta classe de central."
        )
    else:
        linhas.append("  * Sistema de resfriamento por água: Não exigido para esta capacidade de armazenamento.")
    linhas.append("-" * w)

    linhas.append("4. AUDITORIA DOS AFASTAMENTOS MÍNIMOS DE SEGURANÇA (NBR 13523)")
    for idx, item in enumerate(res.auditoria_afastamentos, start=1):
        st_item = "CONFORME" if item.conforme else "INCONFORME"
        linhas.append(f"  [{idx:02d}] {item.item} [{st_item}]")
        linhas.append(
            f"       Distância Exigida: {_fmt(item.distancia_exigida_m, 2)} m | "
            f"Distância Real Medida: {_fmt(item.distancia_real_m, 2)} m"
        )
        linhas.append(f"       Parecer: {item.observacao}")
        linhas.append("  " + "." * (w - 4))

    if res.alertas_tecnicos:
        linhas.append("-" * w)
        linhas.append("5. ALERTAS E INCONFORMIDADES REGULAMENTARES")
        for alerta in res.alertas_tecnicos:
            linhas.append(f"  [ALERTA] {alerta}")

    linhas.append("=" * w)
    linhas.append("Emitido via Lofrano Tecnologia - Conforme ABNT NBR 13523:2019")
    linhas.append("=" * w)

    return "\n".join(linhas)


def gerar_csv_afastamentos(res: ResultadoCentralGLP) -> str:
    """Gera tabela CSV sanitizada contra injeção de fórmulas com auditoria de afastamentos."""
    saida = io.StringIO()
    writer = csv.writer(saida, delimiter=";", lineterminator="\n")

    writer.writerow([
        _sanitizar_campo_csv("item_afastamento"),
        _sanitizar_campo_csv("distancia_exigida_m"),
        _sanitizar_campo_csv("distancia_real_m"),
        _sanitizar_campo_csv("conforme"),
        _sanitizar_campo_csv("observacao"),
    ])

    for a in res.auditoria_afastamentos:
        writer.writerow([
            _sanitizar_campo_csv(a.item),
            _fmt(a.distancia_exigida_m, 2),
            _fmt(a.distancia_real_m, 2),
            "SIM" if a.conforme else "NAO",
            _sanitizar_campo_csv(a.observacao),
        ])

    return saida.getvalue()


def gerar_pacote_zip_central_glp(
    res: ResultadoCentralGLP,
    caminho_zip: str,
    svg_conteudo: Optional[str] = None,
) -> None:
    """Gera pacote determinístico ZIP com O_EXCL, evitando sobrescrita acidental."""
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    fd = os.open(caminho_zip, flags, 0o644)
    fixed_time = (2026, 1, 1, 0, 0, 0)

    try:
        with open(fd, "wb", closefd=True) as f_out:
            with zipfile.ZipFile(f_out, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                # 1. Memorial descritivo em texto
                txt = gerar_relatorio_central_glp_texto(res).encode("utf-8")
                zi_txt = zipfile.ZipInfo(filename="memorial_central_glp.txt", date_time=fixed_time)
                zf.writestr(zi_txt, txt)

                # 2. Dados em JSON canônico
                js = exportar_resultado_json(res).encode("utf-8")
                zi_js = zipfile.ZipInfo(filename="dados_central_glp.json", date_time=fixed_time)
                zf.writestr(zi_js, js)

                # 3. Resumo tabular em CSV sanitizado
                csv_data = gerar_csv_afastamentos(res).encode("utf-8")
                zi_csv = zipfile.ZipInfo(filename="afastamentos_seguranca.csv", date_time=fixed_time)
                zf.writestr(zi_csv, csv_data)

                # 4. Diagrama vetorial SVG se fornecido
                if svg_conteudo is not None:
                    zi_svg = zipfile.ZipInfo(filename="painel_central_glp.svg", date_time=fixed_time)
                    zf.writestr(zi_svg, svg_conteudo.encode("utf-8"))
    except Exception:
        if os.path.exists(caminho_zip):
            try:
                os.remove(caminho_zip)
            except OSError:
                pass
        raise
