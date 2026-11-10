"""Testes unitários para o gerador de painel vetorial SVG."""

import unittest
from fractions import Fraction

from central_glp_nbr13523.models import (
    ClasseCentral,
    ResultadoCentralGLP,
    ResultadoItemAfastamento,
    ResultadoVaporizacao,
    TipoConsumidor,
    TipoRecipiente,
)
from central_glp_nbr13523.svg_generator import gerar_painel_svg


class TestSvg(unittest.TestCase):
    def test_gerar_painel_svg(self):
        res_item = ResultadoItemAfastamento(
            item="Aberturas de Edificações",
            distancia_exigida_m=Fraction(3, 1),
            distancia_real_m=Fraction(7, 2),
            conforme=True,
            observacao="Atende ao afastamento normativo",
        )
        res_vap = ResultadoVaporizacao(
            consumo_pico_kg_h=Fraction(5, 1),
            taxa_vaporizacao_por_recipiente_kg_h=Fraction(1, 1),
            recipientes_servico_minimos_requeridos=5,
            recipientes_servico_especificados=6,
            capacidade_vaporizacao_total_kg_h=Fraction(6, 1),
            vaporizacao_atende=True,
            necessita_vaporizador_artificial=False,
        )
        res = ResultadoCentralGLP(
            identificacao_projeto="Condomínio Teste SVG",
            tipo_consumidor=TipoConsumidor.RESIDENCIAL_COLETIVO,
            tipo_recipiente=TipoRecipiente.P_45,
            classe_central=ClasseCentral.CLASSE_II,
            volume_total_m3=Fraction(1296, 1000),
            capacidade_massa_total_kg=540,
            total_recipientes=12,
            configuracao_bateria="Bateria Dupla 6+6",
            resultado_vaporizacao=res_vap,
            capacidade_minima_regulador_1_estagio_kg_h=Fraction(6, 1),
            pressao_saida_1_estagio_bar=Fraction(3, 2),
            pressao_servico_kpa=Fraction(28, 10),
            extintores_minimos_qtd=2,
            extintores_capacidade_min="20-B:C",
            exige_resfriamento_agua=False,
            auditoria_afastamentos=[res_item],
            conformidade_afastamentos=True,
            conformidade_geral=True,
            alertas_tecnicos=["Observar sinalização de advertência"],
        )
        svg = gerar_painel_svg(res)
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.strip().endswith("</svg>"))
        self.assertIn('viewBox="0 0 1440 900"', svg)
        self.assertIn("LOFRANO TECNOLOGIA", svg)
        self.assertIn("Condomínio Teste SVG", svg)
        self.assertIn("CLASSE_II", svg)
        self.assertIn("CONFORME NBR 13523", svg)
        self.assertIn("ABRIGO DA CENTRAL GLP", svg)


if __name__ == "__main__":
    unittest.main()
