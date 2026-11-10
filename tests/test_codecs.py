"""Testes unitários para codecs JSON RFC 8259 da NBR 13523:2019."""

import json
import unittest
from fractions import Fraction

from central_glp_nbr13523.codecs import (
    _para_fracao,
    carregar_central_glp_json,
    exportar_resultado_json,
)
from central_glp_nbr13523.models import (
    ClasseCentral,
    DadosCentralGLP,
    ResultadoCentralGLP,
    ResultadoItemAfastamento,
    ResultadoVaporizacao,
    TipoConsumidor,
    TipoRecipiente,
)


class TestCodecs(unittest.TestCase):
    def test_para_fracao_tipos(self):
        self.assertEqual(_para_fracao(5), Fraction(5, 1))
        self.assertEqual(_para_fracao("3/2"), Fraction(3, 2))
        self.assertEqual(_para_fracao("1.5"), Fraction(3, 2))
        self.assertEqual(_para_fracao(Fraction(7, 4)), Fraction(7, 4))
        with self.assertRaises(ValueError):
            _para_fracao([1, 2])

    def test_rejeicao_float(self):
        json_invalido = '{"identificacao_projeto": "Teste", "consumo_pico_kg_h": 4.5}'
        with self.assertRaises(ValueError) as ctx:
            carregar_central_glp_json(json_invalido)
        self.assertIn("Ponto flutuante IEEE-754", str(ctx.exception))

    def test_rejeicao_bom(self):
        json_bom = '\ufeff{"identificacao_projeto": "Teste"}'
        with self.assertRaises(ValueError) as ctx:
            carregar_central_glp_json(json_bom)
        self.assertIn("BOM", str(ctx.exception))

    def test_rejeicao_chave_duplicada(self):
        json_dup = '{"identificacao_projeto": "A", "identificacao_projeto": "B"}'
        with self.assertRaises(ValueError) as ctx:
            carregar_central_glp_json(json_dup)
        self.assertIn("Chave duplicada", str(ctx.exception))

    def test_rejeicao_profundidade_excessiva(self):
        d = {}
        atual = d
        for i in range(35):
            atual["next"] = {}
            atual = atual["next"]
        with self.assertRaises(ValueError) as ctx:
            carregar_central_glp_json(json.dumps(d))
        self.assertIn("Profundidade", str(ctx.exception))

    def test_rejeicao_json_nao_objeto(self):
        with self.assertRaises(ValueError):
            carregar_central_glp_json("[]")

    def test_carregamento_valido(self):
        json_valido = """{
          "identificacao_projeto": "Central Condomínio",
          "tipo_consumidor": "RESIDENCIAL_COLETIVO",
          "tipo_recipiente": "P_45",
          "recipientes_em_servico": 6,
          "recipientes_em_reserva": 6,
          "consumo_pico_kg_h": "5",
          "afastamentos": {
            "distancia_aberturas_m": "3.5",
            "distancia_divisa_lote_m": "3.0",
            "distancia_fontes_ignicao_m": "4.0",
            "distancia_ralos_depressoes_m": "2.0",
            "distancia_tanques_inflamaveis_m": "10.0"
          }
        }"""
        dados = carregar_central_glp_json(json_valido)
        self.assertIsInstance(dados, DadosCentralGLP)
        self.assertEqual(dados.identificacao_projeto, "Central Condomínio")
        self.assertEqual(dados.recipientes_em_servico, 6)
        self.assertEqual(dados.consumo_pico_kg_h, Fraction(5, 1))

    def test_exportar_resultado_json(self):
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
            identificacao_projeto="Teste Export",
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
        saida_js = exportar_resultado_json(res)
        self.assertIn("ABNT NBR 13523:2019", saida_js)
        parsed = json.loads(saida_js)
        self.assertEqual(parsed["classe_central"], "CLASSE_II")
        self.assertTrue(parsed["conformidade_geral"])


if __name__ == "__main__":
    unittest.main()
