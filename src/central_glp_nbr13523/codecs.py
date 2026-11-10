"""Codec JSON canônico RFC 8259 para dimensionamento de Centrais de GLP NBR 13523:2019.

Garante ausência estrita de ponto flutuante IEEE-754, rejeição de BOM, verificação de
chaves duplicadas e limitação de profundidade estrutural.
"""

import json
from enum import Enum
from fractions import Fraction
from typing import Any, List

from central_glp_nbr13523.models import (
    DadosAfastamentosReais,
    DadosCentralGLP,
    DadosEquipamentoConsumo,
    DadosMuroProtecao,
    ResultadoCentralGLP,
    TipoConsumidor,
    TipoRecipiente,
    TipoRegulagemPressao,
)


def _rejeitar_float(valor: str) -> None:
    raise ValueError(
        f"Ponto flutuante IEEE-754 ({valor}) não é permitido. "
        "Utilize inteiros ou strings numéricas fracionárias/decimais exatas."
    )


def _rejeitar_chaves_duplicadas(pares: list[tuple[str, Any]]) -> dict[str, Any]:
    resultado: dict[str, Any] = {}
    for chave, valor in pares:
        if chave in resultado:
            raise ValueError(f"Chave duplicada encontrada no JSON: '{chave}'")
        resultado[chave] = valor
    return resultado


def _verificar_profundidade(obj: Any, profundidade: int = 1, limite: int = 32) -> None:
    if profundidade > limite:
        raise ValueError(
            f"Profundidade da estrutura JSON ({profundidade}) excede o limite máximo permitido de {limite}."
        )
    if isinstance(obj, dict):
        for v in obj.values():
            _verificar_profundidade(v, profundidade + 1, limite)
    elif isinstance(obj, list):
        for elem in obj:
            _verificar_profundidade(elem, profundidade + 1, limite)


def _para_fracao(val: Any) -> Fraction:
    if isinstance(val, (int, str)):
        return Fraction(val)
    if isinstance(val, Fraction):
        return val
    raise ValueError(f"Tipo inválido para conversão fracionária: {type(val).__name__} ({val})")


def _serializar_valor(val: Any) -> Any:
    if isinstance(val, Fraction):
        if val.denominator == 1:
            return val.numerator
        return f"{val.numerator}/{val.denominator}"
    if isinstance(val, Enum):
        return val.value
    if isinstance(val, tuple):
        return [_serializar_valor(x) for x in val]
    if isinstance(val, list):
        return [_serializar_valor(x) for x in val]
    if isinstance(val, dict):
        return {k: _serializar_valor(v) for k, v in val.items()}
    return val


def carregar_central_glp_json(conteudo: str) -> DadosCentralGLP:
    """Carrega e valida a central de GLP a partir de string JSON canônica RFC 8259."""
    if conteudo.startswith(("\ufeff", "\xef\xbb\xbf")):
        raise ValueError("Byte Order Mark (BOM) detectado. O arquivo deve ser codificado em UTF-8 puro.")

    try:
        dados = json.loads(
            conteudo,
            object_pairs_hook=_rejeitar_chaves_duplicadas,
            parse_float=_rejeitar_float,
        )
    except json.JSONDecodeError as err:
        raise ValueError(f"Erro de decodificação JSON: {err}") from err

    _verificar_profundidade(dados)

    if not isinstance(dados, dict):
        raise ValueError("O JSON raiz do projeto deve ser um objeto dicionário.")

    identificacao = str(dados.get("identificacao_projeto", "Central de GLP"))

    tipo_cons_str = str(dados.get("tipo_consumidor", "RESIDENCIAL_COLETIVO")).upper()
    try:
        tipo_consumidor = TipoConsumidor(tipo_cons_str)
    except ValueError:
        tipo_consumidor = TipoConsumidor.RESIDENCIAL_COLETIVO

    tipo_rec_str = str(dados.get("tipo_recipiente", "P_45")).upper()
    try:
        tipo_recipiente = TipoRecipiente(tipo_rec_str)
    except ValueError:
        raise ValueError(f"Tipo de recipiente inválido: {tipo_rec_str}")

    rec_servico = int(dados.get("recipientes_em_servico", 2))
    rec_reserva = int(dados.get("recipientes_em_reserva", 2))
    consumo_pico = _para_fracao(dados.get("consumo_pico_kg_h", 2))

    tipo_reg_str = str(dados.get("tipo_regulagem", "BAIXA_PRESSAO_2_8_KPA")).upper()
    try:
        tipo_regulagem = TipoRegulagemPressao(tipo_reg_str)
    except ValueError:
        tipo_regulagem = TipoRegulagemPressao.BAIXA_PRESSAO_2_8_KPA

    responsavel = str(dados.get("responsavel_tecnico", "Engenharia Lofrano"))

    # Afastamentos
    afast_raw = dados.get("afastamentos")
    if not isinstance(afast_raw, dict):
        raise ValueError("O campo 'afastamentos' deve ser um objeto JSON.")

    afastamentos = DadosAfastamentosReais(
        distancia_aberturas_m=_para_fracao(afast_raw.get("distancia_aberturas_m", 3)),
        distancia_divisa_lote_m=_para_fracao(afast_raw.get("distancia_divisa_lote_m", 3)),
        distancia_fontes_ignicao_m=_para_fracao(afast_raw.get("distancia_fontes_ignicao_m", 3)),
        distancia_ralos_depressoes_m=_para_fracao(afast_raw.get("distancia_ralos_depressoes_m", Fraction(3, 2))),
        distancia_tanques_inflamaveis_m=_para_fracao(afast_raw.get("distancia_tanques_inflamaveis_m", 10)),
    )

    # Muro de proteção opcional
    muro_raw = dados.get("muro_protecao", {})
    if isinstance(muro_raw, dict) and muro_raw.get("possui_muro", False):
        muro = DadosMuroProtecao(
            possui_muro=True,
            altura_m=_para_fracao(muro_raw.get("altura_m", Fraction(9, 5))),
            trrf_min=int(muro_raw.get("trrf_min", 120)),
            distancia_pelo_contorno_m=_para_fracao(muro_raw.get("distancia_pelo_contorno_m", 3)),
        )
    else:
        muro = DadosMuroProtecao(possui_muro=False)

    # Equipamentos consumidores opcionais
    equipamentos_raw = dados.get("equipamentos", [])
    equipamentos_parsed: List[DadosEquipamentoConsumo] = []
    if isinstance(equipamentos_raw, list):
        for idx_eq, eq in enumerate(equipamentos_raw):
            if isinstance(eq, dict):
                eq_id = str(eq.get("id", f"EQ-{idx_eq + 1:02d}"))
                desc = str(eq.get("descricao", "Equipamento GLP"))
                consumo = _para_fracao(eq.get("consumo_kg_h", 1))
                fator_sim = _para_fracao(eq.get("fator_simultaneidade", 1))
                equipamentos_parsed.append(
                    DadosEquipamentoConsumo(
                        id=eq_id,
                        descricao=desc,
                        consumo_kg_h=consumo,
                        fator_simultaneidade=fator_sim,
                    )
                )

    return DadosCentralGLP(
        identificacao_projeto=identificacao,
        tipo_consumidor=tipo_consumidor,
        tipo_recipiente=tipo_recipiente,
        recipientes_em_servico=rec_servico,
        recipientes_em_reserva=rec_reserva,
        consumo_pico_kg_h=consumo_pico,
        afastamentos=afastamentos,
        muro_protecao=muro,
        tipo_regulagem=tipo_regulagem,
        responsavel_tecnico=responsavel,
        equipamentos=equipamentos_parsed,
    )


def exportar_resultado_json(resultado: ResultadoCentralGLP) -> str:
    """Serializa o resultado em JSON canônico RFC 8259 determinístico."""
    dados: dict[str, Any] = {
        "norma": "ABNT NBR 13523:2019",
        "identificacao_projeto": resultado.identificacao_projeto,
        "tipo_consumidor": resultado.tipo_consumidor.value,
        "tipo_recipiente": resultado.tipo_recipiente.value,
        "classe_central": resultado.classe_central.value,
        "volume_total_m3": _serializar_valor(resultado.volume_total_m3),
        "capacidade_massa_total_kg": resultado.capacidade_massa_total_kg,
        "total_recipientes": resultado.total_recipientes,
        "configuracao_bateria": resultado.configuracao_bateria,
        "resultado_vaporizacao": {
            "consumo_pico_kg_h": _serializar_valor(resultado.resultado_vaporizacao.consumo_pico_kg_h),
            "taxa_vaporizacao_por_recipiente_kg_h": _serializar_valor(
                resultado.resultado_vaporizacao.taxa_vaporizacao_por_recipiente_kg_h
            ),
            "recipientes_servico_minimos_requeridos": resultado.resultado_vaporizacao.recipientes_servico_minimos_requeridos,
            "recipientes_servico_especificados": resultado.resultado_vaporizacao.recipientes_servico_especificados,
            "capacidade_vaporizacao_total_kg_h": _serializar_valor(
                resultado.resultado_vaporizacao.capacidade_vaporizacao_total_kg_h
            ),
            "vaporizacao_atende": resultado.resultado_vaporizacao.vaporizacao_atende,
            "necessita_vaporizador_artificial": resultado.resultado_vaporizacao.necessita_vaporizador_artificial,
        },
        "regulagem_pressao": {
            "capacidade_minima_regulador_1_estagio_kg_h": _serializar_valor(
                resultado.capacidade_minima_regulador_1_estagio_kg_h
            ),
            "pressao_saida_1_estagio_bar": _serializar_valor(resultado.pressao_saida_1_estagio_bar),
            "pressao_servico_kpa": _serializar_valor(resultado.pressao_servico_kpa),
        },
        "protecao_incendio": {
            "extintores_minimos_qtd": resultado.extintores_minimos_qtd,
            "extintores_capacidade_min": resultado.extintores_capacidade_min,
            "exige_resfriamento_agua": resultado.exige_resfriamento_agua,
        },
        "auditoria_afastamentos": [
            {
                "item": a.item,
                "distancia_exigida_m": _serializar_valor(a.distancia_exigida_m),
                "distancia_real_m": _serializar_valor(a.distancia_real_m),
                "conforme": a.conforme,
                "observacao": a.observacao,
            }
            for a in resultado.auditoria_afastamentos
        ],
        "conformidade_afastamentos": resultado.conformidade_afastamentos,
        "conformidade_geral": resultado.conformidade_geral,
        "alertas_tecnicos": list(resultado.alertas_tecnicos),
    }

    return json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True)
