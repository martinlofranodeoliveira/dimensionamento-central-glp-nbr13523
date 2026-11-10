"""Testes unitários para modelos e enumerações da NBR 13523:2019."""

import unittest
from fractions import Fraction

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


class TestModels(unittest.TestCase):
    def test_enums_valores(self):
        self.assertEqual(TipoRecipiente.P_45.value, "P_45")
        self.assertEqual(ClasseCentral.CLASSE_II.value, "CLASSE_II")
        self.assertEqual(TipoConsumidor.RESIDENCIAL_COLETIVO.value, "RESIDENCIAL_COLETIVO")
        self.assertEqual(TipoRegulagemPressao.BAIXA_PRESSAO_2_8_KPA.value, "BAIXA_PRESSAO_2_8_KPA")

    def test_dados_muro_criacao(self):
        muro = DadosMuroProtecao(
            possui_muro=True,
            altura_m=Fraction(2, 1),
            trrf_min=120,
            distancia_pelo_contorno_m=Fraction(7, 1),
        )
        self.assertTrue(muro.possui_muro)
        self.assertEqual(muro.altura_m, Fraction(2, 1))
        self.assertEqual(muro.trrf_min, 120)

    def test_dados_afastamentos_criacao(self):
        afast = DadosAfastamentosReais(
            distancia_aberturas_m=Fraction(4, 1),
            distancia_divisa_lote_m=Fraction(3, 1),
            distancia_fontes_ignicao_m=Fraction(5, 1),
            distancia_ralos_depressoes_m=Fraction(2, 1),
            distancia_tanques_inflamaveis_m=Fraction(15, 1),
        )
        self.assertEqual(afast.distancia_aberturas_m, Fraction(4, 1))

    def test_dados_equipamento_criacao(self):
        eq = DadosEquipamentoConsumo(
            id="EQ-01",
            descricao="Fogão",
            consumo_kg_h=Fraction(3, 1),
            fator_simultaneidade=Fraction(4, 5),
        )
        self.assertEqual(eq.id, "EQ-01")
        self.assertEqual(eq.consumo_kg_h * eq.fator_simultaneidade, Fraction(12, 5))

    def test_resultado_vaporizacao_imutabilidade(self):
        res = ResultadoVaporizacao(
            consumo_pico_kg_h=Fraction(5, 1),
            taxa_vaporizacao_por_recipiente_kg_h=Fraction(1, 1),
            recipientes_servico_minimos_requeridos=5,
            recipientes_servico_especificados=6,
            capacidade_vaporizacao_total_kg_h=Fraction(6, 1),
            vaporizacao_atende=True,
            necessita_vaporizador_artificial=False,
        )
        self.assertTrue(res.vaporizacao_atende)
        with self.assertRaises(Exception):
            res.vaporizacao_atende = False  # type: ignore

    def test_resultado_central_criacao(self):
        res_item = ResultadoItemAfastamento(
            item="Aberturas",
            distancia_exigida_m=Fraction(3, 1),
            distancia_real_m=Fraction(4, 1),
            conforme=True,
            observacao="OK",
        )
        res_vap = ResultadoVaporizacao(
            consumo_pico_kg_h=Fraction(2, 1),
            taxa_vaporizacao_por_recipiente_kg_h=Fraction(1, 1),
            recipientes_servico_minimos_requeridos=2,
            recipientes_servico_especificados=2,
            capacidade_vaporizacao_total_kg_h=Fraction(2, 1),
            vaporizacao_atende=True,
            necessita_vaporizador_artificial=False,
        )
        res = ResultadoCentralGLP(
            identificacao_projeto="Teste Central",
            tipo_consumidor=TipoConsumidor.RESIDENCIAL_COLETIVO,
            tipo_recipiente=TipoRecipiente.P_45,
            classe_central=ClasseCentral.CLASSE_II,
            volume_total_m3=Fraction(12, 10),
            capacidade_massa_total_kg=540,
            total_recipientes=12,
            configuracao_bateria="Bateria Dupla 6+6",
            resultado_vaporizacao=res_vap,
            capacidade_minima_regulador_1_estagio_kg_h=Fraction(3, 1),
            pressao_saida_1_estagio_bar=Fraction(3, 2),
            pressao_servico_kpa=Fraction(28, 10),
            extintores_minimos_qtd=2,
            extintores_capacidade_min="20-B:C",
            exige_resfriamento_agua=False,
            auditoria_afastamentos=[res_item],
            conformidade_afastamentos=True,
            conformidade_geral=True,
            alertas_tecnicos=[],
        )
        self.assertEqual(res.identificacao_projeto, "Teste Central")
        self.assertTrue(res.conformidade_geral)


if __name__ == "__main__":
    unittest.main()
