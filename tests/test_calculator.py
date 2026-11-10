"""Testes unitários para o motor de cálculo da NBR 13523:2019."""

import unittest
from fractions import Fraction

from central_glp_nbr13523.calculator import (
    auditar_afastamentos,
    auditar_vaporizacao,
    calcular_consumo_efetivo,
    calcular_volume_e_massa_total,
    classificar_classe_central,
    dimensionar_central_glp,
)
from central_glp_nbr13523.models import (
    ClasseCentral,
    DadosAfastamentosReais,
    DadosCentralGLP,
    DadosEquipamentoConsumo,
    DadosMuroProtecao,
    TipoConsumidor,
    TipoRecipiente,
    TipoRegulagemPressao,
)


class TestCalculator(unittest.TestCase):
    def test_classificar_classe_central_fronteiras(self):
        self.assertEqual(classificar_classe_central(Fraction(54, 100)), ClasseCentral.CLASSE_I)
        self.assertEqual(classificar_classe_central(Fraction(55, 100)), ClasseCentral.CLASSE_II)
        self.assertEqual(classificar_classe_central(Fraction(216, 100)), ClasseCentral.CLASSE_II)
        self.assertEqual(classificar_classe_central(Fraction(217, 100)), ClasseCentral.CLASSE_III)
        self.assertEqual(classificar_classe_central(Fraction(540, 100)), ClasseCentral.CLASSE_III)
        self.assertEqual(classificar_classe_central(Fraction(541, 100)), ClasseCentral.CLASSE_IV)
        self.assertEqual(classificar_classe_central(Fraction(1620, 100)), ClasseCentral.CLASSE_IV)
        self.assertEqual(classificar_classe_central(Fraction(1621, 100)), ClasseCentral.CLASSE_V)
        self.assertEqual(classificar_classe_central(Fraction(3240, 100)), ClasseCentral.CLASSE_V)
        self.assertEqual(classificar_classe_central(Fraction(3241, 100)), ClasseCentral.CLASSE_VI)
        self.assertEqual(classificar_classe_central(Fraction(6480, 100)), ClasseCentral.CLASSE_VI)

    def test_classificar_classe_central_erros(self):
        with self.assertRaises(ValueError):
            classificar_classe_central(Fraction(0, 1))
        with self.assertRaises(ValueError):
            classificar_classe_central(Fraction(-1, 1))
        with self.assertRaises(ValueError):
            classificar_classe_central(Fraction(65, 1))

    def test_calcular_volume_e_massa_total(self):
        vol, massa = calcular_volume_e_massa_total(TipoRecipiente.P_45, 12)
        # 12 * 0.108 = 1.296 m³ = 1296/1000 = 162/125
        self.assertEqual(vol, Fraction(162, 125))
        self.assertEqual(massa, 540)

        vol_e, massa_e = calcular_volume_e_massa_total(TipoRecipiente.E_2000, 2)
        # 2 * 4.8 = 9.6 m³
        self.assertEqual(vol_e, Fraction(48, 5))
        self.assertEqual(massa_e, 4000)

    def test_calcular_consumo_efetivo(self):
        # Sem equipamentos
        self.assertEqual(calcular_consumo_efetivo(Fraction(5, 1), []), Fraction(5, 1))

        # Com equipamentos
        eq1 = DadosEquipamentoConsumo("E1", "Desc", Fraction(4, 1), Fraction(1, 1))
        eq2 = DadosEquipamentoConsumo("E2", "Desc", Fraction(6, 1), Fraction(1, 2))
        # Total eq = 4 + 3 = 7 kg/h
        self.assertEqual(calcular_consumo_efetivo(Fraction(5, 1), [eq1, eq2]), Fraction(7, 1))
        # Se consumo informado for maior, prevalece o maior
        self.assertEqual(calcular_consumo_efetivo(Fraction(10, 1), [eq1, eq2]), Fraction(10, 1))

    def test_auditar_vaporizacao_sucesso(self):
        # P-45 vaporiza 1.0 kg/h por cilindro
        # Consumo de 5.5 kg/h com 6 cilindros em serviço -> 6.0 kg/h >= 5.5 kg/h -> OK
        res = auditar_vaporizacao(TipoRecipiente.P_45, Fraction(11, 2), 6)
        self.assertTrue(res.vaporizacao_atende)
        self.assertFalse(res.necessita_vaporizador_artificial)
        self.assertEqual(res.recipientes_servico_minimos_requeridos, 6)
        self.assertEqual(res.capacidade_vaporizacao_total_kg_h, Fraction(6, 1))

    def test_auditar_vaporizacao_insuficiente(self):
        # P-45: consumo de 8 kg/h com apenas 4 cilindros em serviço -> 4.0 kg/h < 8.0 kg/h -> Insuficiente
        res = auditar_vaporizacao(TipoRecipiente.P_45, Fraction(8, 1), 4)
        self.assertFalse(res.vaporizacao_atende)
        self.assertTrue(res.necessita_vaporizador_artificial)
        self.assertEqual(res.recipientes_servico_minimos_requeridos, 8)

    def test_auditar_afastamentos_diretos_conformes(self):
        afast = DadosAfastamentosReais(
            distancia_aberturas_m=Fraction(4, 1),     # Req Classe II: 3.0m
            distancia_divisa_lote_m=Fraction(4, 1),   # Req Classe II: 3.0m
            distancia_fontes_ignicao_m=Fraction(4, 1),# Req Classe II: 3.0m
            distancia_ralos_depressoes_m=Fraction(2, 1),# Req Classe II: 1.5m
            distancia_tanques_inflamaveis_m=Fraction(10, 1),# Req: 6.0m
        )
        itens, conf, alertas = auditar_afastamentos(
            ClasseCentral.CLASSE_II, afast, DadosMuroProtecao(False)
        )
        self.assertTrue(conf)
        self.assertEqual(len(alertas), 0)
        self.assertEqual(len(itens), 5)
        self.assertTrue(all(i.conforme for i in itens))

    def test_auditar_afastamentos_compensacao_muro_sucesso(self):
        # Divisa a 1.5m em Classe II (exige 3.0m), mas possui muro corta-fogo válido com contorno de 3.5m >= 3.0m
        afast = DadosAfastamentosReais(
            distancia_aberturas_m=Fraction(4, 1),
            distancia_divisa_lote_m=Fraction(3, 2),  # 1.5m < 3.0m
            distancia_fontes_ignicao_m=Fraction(4, 1),
            distancia_ralos_depressoes_m=Fraction(2, 1),
            distancia_tanques_inflamaveis_m=Fraction(10, 1),
        )
        muro = DadosMuroProtecao(
            possui_muro=True,
            altura_m=Fraction(2, 1),  # >= 1.80m
            trrf_min=120,            # >= 120min
            distancia_pelo_contorno_m=Fraction(7, 2), # 3.5m >= 3.0m
        )
        itens, conf, alertas = auditar_afastamentos(ClasseCentral.CLASSE_II, afast, muro)
        self.assertTrue(conf)
        self.assertTrue(any("compensada por muro" in i.observacao for i in itens))

    def test_auditar_afastamentos_muro_invalido_reprova(self):
        # Muro com altura insuficiente (1.50m < 1.80m)
        afast = DadosAfastamentosReais(
            distancia_aberturas_m=Fraction(4, 1),
            distancia_divisa_lote_m=Fraction(3, 2),
            distancia_fontes_ignicao_m=Fraction(4, 1),
            distancia_ralos_depressoes_m=Fraction(2, 1),
            distancia_tanques_inflamaveis_m=Fraction(10, 1),
        )
        muro = DadosMuroProtecao(
            possui_muro=True,
            altura_m=Fraction(3, 2),  # 1.50m < 1.80m -> inválido!
            trrf_min=120,
            distancia_pelo_contorno_m=Fraction(5, 1),
        )
        _, conf, alertas = auditar_afastamentos(ClasseCentral.CLASSE_II, afast, muro)
        self.assertFalse(conf)
        self.assertGreater(len(alertas), 0)

    def test_dimensionar_central_glp_completo(self):
        dados = DadosCentralGLP(
            identificacao_projeto="Central Teste Edifício",
            tipo_consumidor=TipoConsumidor.RESIDENCIAL_COLETIVO,
            tipo_recipiente=TipoRecipiente.P_45,
            recipientes_em_servico=6,
            recipientes_em_reserva=6,
            consumo_pico_kg_h=Fraction(5, 1),
            afastamentos=DadosAfastamentosReais(
                distancia_aberturas_m=Fraction(4, 1),
                distancia_divisa_lote_m=Fraction(4, 1),
                distancia_fontes_ignicao_m=Fraction(4, 1),
                distancia_ralos_depressoes_m=Fraction(2, 1),
                distancia_tanques_inflamaveis_m=Fraction(10, 1),
            ),
            tipo_regulagem=TipoRegulagemPressao.BAIXA_PRESSAO_2_8_KPA,
        )
        res = dimensionar_central_glp(dados)
        self.assertEqual(res.classe_central, ClasseCentral.CLASSE_II)
        self.assertEqual(res.total_recipientes, 12)
        self.assertEqual(res.capacidade_massa_total_kg, 540)
        self.assertTrue(res.conformidade_geral)
        self.assertEqual(res.capacidade_minima_regulador_1_estagio_kg_h, Fraction(6, 1)) # 5 * 1.2 = 6.0


if __name__ == "__main__":
    unittest.main()
