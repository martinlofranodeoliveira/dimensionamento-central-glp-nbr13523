"""Motor determinístico de dimensionamento e auditoria de Centrais de GLP.

Em conformidade estrita com a ABNT NBR 13523:2019 e Corpo de Bombeiros.
Aritmética estritamente racional e inteira (Zero-Float).
"""

from fractions import Fraction
from typing import List, Tuple

from central_glp_nbr13523.constants import (
    ALTURA_MINIMA_MURO_PROTECAO_M,
    CATALOGO_RECIPIENTES,
    FATOR_SOBRECAPACIDADE_REGULADOR_1_ESTAGIO,
    LIMITES_CLASSE_VOLUME_M3,
    PRESSAO_BAIXA_SERVICO_KPA,
    PRESSAO_MEDIA_SERVICO_KPA,
    PRESSAO_SAIDA_1_ESTAGIO_BAR,
    TABELA_AFASTAMENTOS,
    TRRF_MINIMO_MURO_PROTECAO_MIN,
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
    TipoRecipiente,
    TipoRegulagemPressao,
)


def classificar_classe_central(volume_total_m3: Fraction) -> ClasseCentral:
    """Classifica a Central de GLP conforme o volume total em m³ (Tabela 1/2)."""
    if volume_total_m3 <= Fraction(0, 1):
        raise ValueError(f"Volume total da central deve ser estritamente positivo: {volume_total_m3} m³")

    for nome_classe, limite_vol in LIMITES_CLASSE_VOLUME_M3:
        if volume_total_m3 <= limite_vol:
            return ClasseCentral(nome_classe)

    raise ValueError(
        f"Volume total de {volume_total_m3} m³ excede o limite normativo da Classe VI (64.80 m³). "
        "Instalação requer projeto especial de engenharia de processo industrial e bombeiros."
    )


def calcular_volume_e_massa_total(
    tipo_recipiente: TipoRecipiente, total_recipientes: int
) -> Tuple[Fraction, int]:
    """Calcula o volume geométrico total em m³ e a massa total nominal em kg."""
    if total_recipientes <= 0:
        raise ValueError(f"Quantidade total de recipientes deve ser maior que zero: {total_recipientes}")

    spec = CATALOGO_RECIPIENTES.get(tipo_recipiente.value)
    if spec is None:
        raise ValueError(f"Tipo de recipiente não reconhecido: {tipo_recipiente}")

    volume_total = spec.volume_m3 * total_recipientes
    massa_total = spec.capacidade_massa_kg * total_recipientes
    return volume_total, massa_total


def calcular_consumo_efetivo(
    consumo_informado: Fraction, equipamentos: List[DadosEquipamentoConsumo]
) -> Fraction:
    """Calcula o consumo de pico efetivo levando em conta equipamentos cadastrados."""
    if not equipamentos:
        return consumo_informado

    soma_equipamentos = Fraction(0, 1)
    for eq in equipamentos:
        soma_equipamentos += eq.consumo_kg_h * eq.fator_simultaneidade

    if soma_equipamentos > Fraction(0, 1):
        return max(consumo_informado, soma_equipamentos)
    return consumo_informado


def auditar_vaporizacao(
    tipo_recipiente: TipoRecipiente, consumo_pico_kg_h: Fraction, recipientes_servico: int
) -> ResultadoVaporizacao:
    """Audita se a taxa de vaporização natural atende ao consumo de pico."""
    if consumo_pico_kg_h <= Fraction(0, 1):
        raise ValueError(f"Consumo de pico de GLP deve ser maior que zero: {consumo_pico_kg_h} kg/h")
    if recipientes_servico <= 0:
        raise ValueError(f"Recipientes em serviço deve ser pelo menos 1: {recipientes_servico}")

    spec = CATALOGO_RECIPIENTES[tipo_recipiente.value]
    taxa_unit = spec.taxa_vaporizacao_natural_kg_h

    # Teto inteiro exato da divisão racional: ceil(consumo_pico / taxa_unit)
    razao = consumo_pico_kg_h / taxa_unit
    recipientes_requeridos = razao.numerator // razao.denominator
    if razao.numerator % razao.denominator != 0:
        recipientes_requeridos += 1

    capacidade_vaporizacao_total = taxa_unit * recipientes_servico
    vaporizacao_atende = capacidade_vaporizacao_total >= consumo_pico_kg_h
    necessita_vaporizador = not vaporizacao_atende

    return ResultadoVaporizacao(
        consumo_pico_kg_h=consumo_pico_kg_h,
        taxa_vaporizacao_por_recipiente_kg_h=taxa_unit,
        recipientes_servico_minimos_requeridos=recipientes_requeridos,
        recipientes_servico_especificados=recipientes_servico,
        capacidade_vaporizacao_total_kg_h=capacidade_vaporizacao_total,
        vaporizacao_atende=vaporizacao_atende,
        necessita_vaporizador_artificial=necessita_vaporizador,
    )


def auditar_afastamentos(
    classe: ClasseCentral,
    afastamentos: DadosAfastamentosReais,
    muro: DadosMuroProtecao,
) -> Tuple[List[ResultadoItemAfastamento], bool, List[str]]:
    """Audita os afastamentos de segurança reais contra as distâncias normativas da classe."""
    tab = TABELA_AFASTAMENTOS[classe.value]
    itens: List[ResultadoItemAfastamento] = []
    alertas: List[str] = []
    conformidade_geral = True

    # 1. Aberturas de edificações habitáveis
    exigida_aberturas = tab.aberturas_edificacoes_m
    real_aberturas = afastamentos.distancia_aberturas_m
    conforme_aberturas = real_aberturas >= exigida_aberturas
    obs_aberturas = "Atende diretamente ao afastamento normativo."

    if not conforme_aberturas:
        if (
            muro.possui_muro
            and muro.altura_m >= ALTURA_MINIMA_MURO_PROTECAO_M
            and muro.trrf_min >= TRRF_MINIMO_MURO_PROTECAO_MIN
            and muro.distancia_pelo_contorno_m >= exigida_aberturas
        ):
            conforme_aberturas = True
            obs_aberturas = (
                f"Distância direta ({real_aberturas}m < {exigida_aberturas}m) compensada por "
                f"muro corta-fogo TRRF {muro.trrf_min}min h={muro.altura_m}m com contorno de "
                f"{muro.distancia_pelo_contorno_m}m >= {exigida_aberturas}m (NBR 13523 Item 5.3)."
            )
        else:
            conformidade_geral = False
            obs_aberturas = (
                f"AFASTAMENTO INSUFICIENTE: distância real {real_aberturas}m < exigida {exigida_aberturas}m "
                "(sem muro corta-fogo compensador válido)."
            )
            alertas.append(f"Aberturas de edificação não atendem ao afastamento mínimo de {exigida_aberturas} m.")

    itens.append(
        ResultadoItemAfastamento(
            item="Aberturas de Edificações (portas, janelas, poços)",
            distancia_exigida_m=exigida_aberturas,
            distancia_real_m=real_aberturas,
            conforme=conforme_aberturas,
            observacao=obs_aberturas,
        )
    )

    # 2. Divisas de lotes vizinhos e alinhamento de via pública
    exigida_divisa = tab.divisa_lote_alinhamento_m
    real_divisa = afastamentos.distancia_divisa_lote_m
    conforme_divisa = real_divisa >= exigida_divisa
    obs_divisa = "Atende diretamente ao afastamento normativo."

    if not conforme_divisa:
        if (
            muro.possui_muro
            and muro.altura_m >= ALTURA_MINIMA_MURO_PROTECAO_M
            and muro.trrf_min >= TRRF_MINIMO_MURO_PROTECAO_MIN
            and muro.distancia_pelo_contorno_m >= exigida_divisa
        ):
            conforme_divisa = True
            obs_divisa = (
                f"Distância direta ({real_divisa}m < {exigida_divisa}m) compensada por "
                f"muro corta-fogo TRRF {muro.trrf_min}min com contorno de "
                f"{muro.distancia_pelo_contorno_m}m >= {exigida_divisa}m."
            )
        else:
            conformidade_geral = False
            obs_divisa = (
                f"AFASTAMENTO INSUFICIENTE: divisa real {real_divisa}m < exigida {exigida_divisa}m."
            )
            alertas.append(f"Divisa de lote/alinhamento predial não atende ao afastamento de {exigida_divisa} m.")

    itens.append(
        ResultadoItemAfastamento(
            item="Divisas de Lotes e Alinhamento de Via Pública",
            distancia_exigida_m=exigida_divisa,
            distancia_real_m=real_divisa,
            conforme=conforme_divisa,
            observacao=obs_divisa,
        )
    )

    # 3. Fontes de ignição e chamas abertas
    exigida_ignicao = tab.fontes_ignicao_m
    real_ignicao = afastamentos.distancia_fontes_ignicao_m
    conforme_ignicao = real_ignicao >= exigida_ignicao
    obs_ignicao = "Atende ao afastamento de segurança contra centelhas e fontes térmicas."

    if not conforme_ignicao:
        conformidade_geral = False
        obs_ignicao = (
            f"PERIGO CRÍTICO DE EXPLOSÃO: fonte de ignição a {real_ignicao}m < exigida {exigida_ignicao}m."
        )
        alertas.append(f"Fontes de ignição a menos de {exigida_ignicao} m dos recipientes de GLP.")

    itens.append(
        ResultadoItemAfastamento(
            item="Fontes de Ignição e Chamas Abertas",
            distancia_exigida_m=exigida_ignicao,
            distancia_real_m=real_ignicao,
            conforme=conforme_ignicao,
            observacao=obs_ignicao,
        )
    )

    # 4. Ralos, depressões, grelhas pluviais e caixas de esgoto
    exigida_ralos = tab.ralos_depressoes_m
    real_ralos = afastamentos.distancia_ralos_depressoes_m
    conforme_ralos = real_ralos >= exigida_ralos
    obs_ralos = "Atende à distância de proteção contra confinamento de GLP gasoso denso."

    if not conforme_ralos:
        conformidade_geral = False
        obs_ralos = (
            f"RISCO GRAVE DE ACÚMULO DE GÁS: ralo/depressão a {real_ralos}m < exigida {exigida_ralos}m. "
            "GLP gasoso é mais denso que o ar e tende a acumular-se em depressões subterrâneas."
        )
        alertas.append(f"Ralos/depressões a menos de {exigida_ralos} m da central (risco de confinamento).")

    itens.append(
        ResultadoItemAfastamento(
            item="Ralos, Depressões e Galerias Pluviais/Esgoto",
            distancia_exigida_m=exigida_ralos,
            distancia_real_m=real_ralos,
            conforme=conforme_ralos,
            observacao=obs_ralos,
        )
    )

    # 5. Outros reservatórios de líquidos combustíveis ou inflamáveis
    exigida_tanques = tab.tanques_inflamaveis_m
    real_tanques = afastamentos.distancia_tanques_inflamaveis_m
    conforme_tanques = real_tanques >= exigida_tanques
    obs_tanques = "Afastamento entre tanques combustíveis plenamente atendido."

    if not conforme_tanques:
        conformidade_geral = False
        obs_tanques = (
            f"AFASTAMENTO INSUFICIENTE: tanque inflamável a {real_tanques}m < exigida {exigida_tanques}m."
        )
        alertas.append(f"Tanques inflamáveis vizinhos a menos de {exigida_tanques} m da central.")

    itens.append(
        ResultadoItemAfastamento(
            item="Tanques de Líquidos Inflamáveis / Combustíveis",
            distancia_exigida_m=exigida_tanques,
            distancia_real_m=real_tanques,
            conforme=conforme_tanques,
            observacao=obs_tanques,
        )
    )

    return itens, conformidade_geral, alertas


def dimensionar_central_glp(dados: DadosCentralGLP) -> ResultadoCentralGLP:
    """Executa o cálculo analítico completo e a auditoria normativa da Central de GLP."""
    if dados.recipientes_em_servico <= 0:
        raise ValueError("Quantidade de recipientes em serviço deve ser no mínimo 1.")
    if dados.recipientes_em_reserva < 0:
        raise ValueError("Quantidade de recipientes em reserva não pode ser negativa.")

    total_recipientes = dados.recipientes_em_servico + dados.recipientes_em_reserva
    volume_total, massa_total = calcular_volume_e_massa_total(dados.tipo_recipiente, total_recipientes)
    classe_central = classificar_classe_central(volume_total)

    consumo_efetivo = calcular_consumo_efetivo(dados.consumo_pico_kg_h, dados.equipamentos)
    res_vaporizacao = auditar_vaporizacao(
        dados.tipo_recipiente, consumo_efetivo, dados.recipientes_em_servico
    )

    itens_afastamento, conformidade_afastamentos, alertas = auditar_afastamentos(
        classe_central, dados.afastamentos, dados.muro_protecao
    )

    if not res_vaporizacao.vaporizacao_atende:
        alertas.append(
            f"Vaporização natural insuficiente ({res_vaporizacao.capacidade_vaporizacao_total_kg_h} kg/h < "
            f"{consumo_efetivo} kg/h). Requer mínimo de {res_vaporizacao.recipientes_servico_minimos_requeridos} "
            f"recipientes em serviço ou Vaporizador Artificial."
        )

    tab = TABELA_AFASTAMENTOS[classe_central.value]
    cap_min_regulador_1 = consumo_efetivo * FATOR_SOBRECAPACIDADE_REGULADOR_1_ESTAGIO
    pressao_saida_1 = PRESSAO_SAIDA_1_ESTAGIO_BAR

    if dados.tipo_regulagem == TipoRegulagemPressao.BAIXA_PRESSAO_2_8_KPA:
        pressao_servico = PRESSAO_BAIXA_SERVICO_KPA
    else:
        pressao_servico = PRESSAO_MEDIA_SERVICO_KPA

    if dados.recipientes_em_reserva > 0:
        config_bateria = (
            f"Bateria Dupla ({dados.recipientes_em_servico} em serviço + "
            f"{dados.recipientes_em_reserva} reserva) - {dados.tipo_recipiente.value}"
        )
    else:
        config_bateria = (
            f"Conjunto Estacionário Único ({dados.recipientes_em_servico} unidades) - {dados.tipo_recipiente.value}"
        )

    conformidade_geral = conformidade_afastamentos and res_vaporizacao.vaporizacao_atende

    return ResultadoCentralGLP(
        identificacao_projeto=dados.identificacao_projeto,
        tipo_consumidor=dados.tipo_consumidor,
        tipo_recipiente=dados.tipo_recipiente,
        classe_central=classe_central,
        volume_total_m3=volume_total,
        capacidade_massa_total_kg=massa_total,
        total_recipientes=total_recipientes,
        configuracao_bateria=config_bateria,
        resultado_vaporizacao=res_vaporizacao,
        capacidade_minima_regulador_1_estagio_kg_h=cap_min_regulador_1,
        pressao_saida_1_estagio_bar=pressao_saida_1,
        pressao_servico_kpa=pressao_servico,
        extintores_minimos_qtd=tab.extintores_minimos_qtd,
        extintores_capacidade_min=tab.extintores_capacidade_min,
        exige_resfriamento_agua=tab.exige_resfriamento_agua,
        auditoria_afastamentos=itens_afastamento,
        conformidade_afastamentos=conformidade_afastamentos,
        conformidade_geral=conformidade_geral,
        alertas_tecnicos=alertas,
    )
