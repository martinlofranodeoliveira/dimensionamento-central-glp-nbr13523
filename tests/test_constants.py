"""Testes unitários para as constantes normativas da NBR 13523:2019."""

import unittest
from fractions import Fraction

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


class TestConstants(unittest.TestCase):
    def test_catalogo_recipientes_completude(self):
        tipos_esperados = ["P_13", "P_20", "P_45", "P_90", "P_190", "E_500", "E_1000", "E_2000", "E_4000"]
        for t in tipos_esperados:
            self.assertIn(t, CATALOGO_RECIPIENTES)
            spec = CATALOGO_RECIPIENTES[t]
            self.assertGreater(spec.capacidade_massa_kg, 0)
            self.assertGreater(spec.volume_m3, Fraction(0, 1))
            self.assertGreater(spec.taxa_vaporizacao_natural_kg_h, Fraction(0, 1))
            self.assertIsInstance(spec.volume_m3, Fraction)
            self.assertIsInstance(spec.taxa_vaporizacao_natural_kg_h, Fraction)

    def test_limites_classes_ordenacao(self):
        self.assertEqual(len(LIMITES_CLASSE_VOLUME_M3), 6)
        limite_anterior = Fraction(0, 1)
        for _, limite in LIMITES_CLASSE_VOLUME_M3:
            self.assertGreater(limite, limite_anterior)
            limite_anterior = limite

    def test_tabela_afastamentos_todas_classes(self):
        classes = ["CLASSE_I", "CLASSE_II", "CLASSE_III", "CLASSE_IV", "CLASSE_V", "CLASSE_VI"]
        for c in classes:
            self.assertIn(c, TABELA_AFASTAMENTOS)
            tab = TABELA_AFASTAMENTOS[c]
            self.assertGreater(tab.aberturas_edificacoes_m, Fraction(0, 1))
            self.assertGreater(tab.divisa_lote_alinhamento_m, Fraction(0, 1))
            self.assertGreater(tab.fontes_ignicao_m, Fraction(0, 1))
            self.assertGreater(tab.ralos_depressoes_m, Fraction(0, 1))
            self.assertGreater(tab.tanques_inflamaveis_m, Fraction(0, 1))
            self.assertGreaterEqual(tab.extintores_minimos_qtd, 1)

    def test_parametros_reguladores_e_muro(self):
        self.assertEqual(FATOR_SOBRECAPACIDADE_REGULADOR_1_ESTAGIO, Fraction(6, 5))
        self.assertEqual(PRESSAO_SAIDA_1_ESTAGIO_BAR, Fraction(3, 2))
        self.assertEqual(PRESSAO_BAIXA_SERVICO_KPA, Fraction(28, 10))
        self.assertEqual(PRESSAO_MEDIA_SERVICO_KPA, Fraction(50, 1))
        self.assertEqual(ALTURA_MINIMA_MURO_PROTECAO_M, Fraction(9, 5))
        self.assertEqual(TRRF_MINIMO_MURO_PROTECAO_MIN, 120)


if __name__ == "__main__":
    unittest.main()
