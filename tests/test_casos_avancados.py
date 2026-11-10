"""Testes para cenários avançados, casos de borda e validação de todos os exemplos."""

import glob
import os
import unittest
from fractions import Fraction

from central_glp_nbr13523.calculator import dimensionar_central_glp
from central_glp_nbr13523.codecs import carregar_central_glp_json
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


class TestCasosAvancados(unittest.TestCase):
    def test_todos_exemplos_carregam_e_dimensionam_com_sucesso(self):
        raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        pasta_exemplos = os.path.join(raiz, "examples")
        arquivos = sorted(glob.glob(os.path.join(pasta_exemplos, "*.json")))
        self.assertGreaterEqual(len(arquivos), 3)

        for arq in arquivos:
            with open(arq, "r", encoding="utf-8") as f:
                dados = carregar_central_glp_json(f.read())
            res = dimensionar_central_glp(dados)
            self.assertTrue(res.conformidade_geral, f"Cenário {os.path.basename(arq)} deve ser conforme!")

    def test_reprovacao_ralo_muito_proximo_perigo_acumulo(self):
        # Ralo de esgoto a 0.8m da central (Classe I exige 1.5m)
        dados = DadosCentralGLP(
            identificacao_projeto="Central com Ralo Irregular",
            tipo_consumidor=TipoConsumidor.COMERCIAL_RESTAURANTE,
            tipo_recipiente=TipoRecipiente.P_45,
            recipientes_em_servico=2,
            recipientes_em_reserva=2,
            consumo_pico_kg_h=Fraction(2, 1),
            afastamentos=DadosAfastamentosReais(
                distancia_aberturas_m=Fraction(3, 1),
                distancia_divisa_lote_m=Fraction(3, 1),
                distancia_fontes_ignicao_m=Fraction(3, 1),
                distancia_ralos_depressoes_m=Fraction(8, 10),  # 0.8m < 1.5m -> Perigo!
                distancia_tanques_inflamaveis_m=Fraction(10, 1),
            ),
        )
        res = dimensionar_central_glp(dados)
        self.assertFalse(res.conformidade_afastamentos)
        self.assertFalse(res.conformidade_geral)
        self.assertTrue(any("Ralos" in a.item and not a.conforme for a in res.auditoria_afastamentos))
        self.assertTrue(any("confinamento" in alerta or "Ralos" in alerta for alerta in res.alertas_tecnicos))

    def test_reprovacao_fonte_ignicao_muito_proxima(self):
        # Fonte de ignição a 1.2m (exige 3.0m)
        dados = DadosCentralGLP(
            identificacao_projeto="Central com Motor Elétrico Próximo",
            tipo_consumidor=TipoConsumidor.INDUSTRIAL,
            tipo_recipiente=TipoRecipiente.P_45,
            recipientes_em_servico=2,
            recipientes_em_reserva=2,
            consumo_pico_kg_h=Fraction(2, 1),
            afastamentos=DadosAfastamentosReais(
                distancia_aberturas_m=Fraction(3, 1),
                distancia_divisa_lote_m=Fraction(3, 1),
                distancia_fontes_ignicao_m=Fraction(6, 5),  # 1.2m < 3.0m
                distancia_ralos_depressoes_m=Fraction(2, 1),
                distancia_tanques_inflamaveis_m=Fraction(10, 1),
            ),
        )
        res = dimensionar_central_glp(dados)
        self.assertFalse(res.conformidade_afastamentos)
        self.assertFalse(res.conformidade_geral)
        self.assertTrue(any("Fontes de Ignição" in a.item and not a.conforme for a in res.auditoria_afastamentos))

    def test_vaporizador_artificial_obrigatorio_por_alta_demanda(self):
        # Consumo de 20 kg/h com apenas 4 cilindros P-45 (capacidade 4.0 kg/h)
        dados = DadosCentralGLP(
            identificacao_projeto="Central Industrial Alta Vazão",
            tipo_consumidor=TipoConsumidor.INDUSTRIAL,
            tipo_recipiente=TipoRecipiente.P_45,
            recipientes_em_servico=4,
            recipientes_em_reserva=4,
            consumo_pico_kg_h=Fraction(20, 1),
            afastamentos=DadosAfastamentosReais(
                distancia_aberturas_m=Fraction(4, 1),
                distancia_divisa_lote_m=Fraction(4, 1),
                distancia_fontes_ignicao_m=Fraction(4, 1),
                distancia_ralos_depressoes_m=Fraction(2, 1),
                distancia_tanques_inflamaveis_m=Fraction(10, 1),
            ),
        )
        res = dimensionar_central_glp(dados)
        self.assertFalse(res.resultado_vaporizacao.vaporizacao_atende)
        self.assertTrue(res.resultado_vaporizacao.necessita_vaporizador_artificial)
        self.assertEqual(res.resultado_vaporizacao.recipientes_servico_minimos_requeridos, 20)
        self.assertFalse(res.conformidade_geral)

    def test_tanque_estacionario_classe_vi(self):
        # 6x E-4000 = 6 * 9.6 m³ = 57.6 m³ (Classe VI: 32.40 < V <= 64.80 m³)
        dados = DadosCentralGLP(
            identificacao_projeto="Parque Industrial de Grande Porte",
            tipo_consumidor=TipoConsumidor.INDUSTRIAL,
            tipo_recipiente=TipoRecipiente.E_4000,
            recipientes_em_servico=6,
            recipientes_em_reserva=0,
            consumo_pico_kg_h=Fraction(300, 1),  # 6 * 60 = 360 kg/h capacity >= 300
            afastamentos=DadosAfastamentosReais(
                distancia_aberturas_m=Fraction(16, 1),      # Req: 15.0m
                distancia_divisa_lote_m=Fraction(16, 1),    # Req: 15.0m
                distancia_fontes_ignicao_m=Fraction(16, 1), # Req: 15.0m
                distancia_ralos_depressoes_m=Fraction(4, 1),# Req: 3.0m
                distancia_tanques_inflamaveis_m=Fraction(16, 1), # Req: 15.0m
            ),
            tipo_regulagem=TipoRegulagemPressao.MEDIA_PRESSAO_50_KPA,
        )
        res = dimensionar_central_glp(dados)
        self.assertEqual(res.classe_central, ClasseCentral.CLASSE_VI)
        self.assertEqual(res.volume_total_m3, Fraction(288, 5)) # 57.6 m³
        self.assertEqual(res.capacidade_massa_total_kg, 24000) # 24 toneladas de GLP
        self.assertTrue(res.exige_resfriamento_agua)
        self.assertEqual(res.extintores_minimos_qtd, 3)
        self.assertTrue(res.conformidade_geral)

    def test_pressao_servico_media_pressao(self):
        dados = DadosCentralGLP(
            identificacao_projeto="Central Média Pressão",
            tipo_consumidor=TipoConsumidor.INDUSTRIAL,
            tipo_recipiente=TipoRecipiente.P_190,
            recipientes_em_servico=2,
            recipientes_em_reserva=2,
            consumo_pico_kg_h=Fraction(5, 1),
            afastamentos=DadosAfastamentosReais(
                distancia_aberturas_m=Fraction(4, 1),
                distancia_divisa_lote_m=Fraction(4, 1),
                distancia_fontes_ignicao_m=Fraction(4, 1),
                distancia_ralos_depressoes_m=Fraction(2, 1),
            ),
            tipo_regulagem=TipoRegulagemPressao.MEDIA_PRESSAO_50_KPA,
        )
        res = dimensionar_central_glp(dados)
        self.assertEqual(res.pressao_servico_kpa, Fraction(50, 1))

    def test_muro_contorno_menor_que_exigido(self):
        # 8x P-45 = 0.864 m³ -> Classe II (exige divisa 3.0m)
        # Muro com altura 2.0m e TRRF 120min, mas contorno de 2.5m < 3.0m
        dados = DadosCentralGLP(
            identificacao_projeto="Muro Curto",
            tipo_consumidor=TipoConsumidor.RESIDENCIAL_COLETIVO,
            tipo_recipiente=TipoRecipiente.P_45,
            recipientes_em_servico=4,
            recipientes_em_reserva=4,
            consumo_pico_kg_h=Fraction(2, 1),
            afastamentos=DadosAfastamentosReais(
                distancia_aberturas_m=Fraction(4, 1),
                distancia_divisa_lote_m=Fraction(1, 1), # 1.0m < 3.0m
                distancia_fontes_ignicao_m=Fraction(4, 1),
                distancia_ralos_depressoes_m=Fraction(2, 1),
            ),
            muro_protecao=DadosMuroProtecao(
                possui_muro=True,
                altura_m=Fraction(2, 1),
                trrf_min=120,
                distancia_pelo_contorno_m=Fraction(5, 2), # 2.5m < 3.0m -> Não atende!
            ),
        )
        res = dimensionar_central_glp(dados)
        self.assertFalse(res.conformidade_geral)
        self.assertFalse(res.conformidade_afastamentos)

    def test_recipientes_em_servico_invalido(self):
        with self.assertRaises(ValueError):
            DadosCentralGLP(
                identificacao_projeto="Erro",
                tipo_consumidor=TipoConsumidor.RESIDENCIAL_COLETIVO,
                tipo_recipiente=TipoRecipiente.P_45,
                recipientes_em_servico=0,
                recipientes_em_reserva=0,
                consumo_pico_kg_h=Fraction(2, 1),
                afastamentos=DadosAfastamentosReais(
                    distancia_aberturas_m=Fraction(3, 1),
                    distancia_divisa_lote_m=Fraction(3, 1),
                    distancia_fontes_ignicao_m=Fraction(3, 1),
                    distancia_ralos_depressoes_m=Fraction(2, 1),
                ),
            )
            dimensionar_central_glp(
                DadosCentralGLP(
                    identificacao_projeto="Erro",
                    tipo_consumidor=TipoConsumidor.RESIDENCIAL_COLETIVO,
                    tipo_recipiente=TipoRecipiente.P_45,
                    recipientes_em_servico=0,
                    recipientes_em_reserva=0,
                    consumo_pico_kg_h=Fraction(2, 1),
                    afastamentos=DadosAfastamentosReais(
                        distancia_aberturas_m=Fraction(3, 1),
                        distancia_divisa_lote_m=Fraction(3, 1),
                        distancia_fontes_ignicao_m=Fraction(3, 1),
                        distancia_ralos_depressoes_m=Fraction(2, 1),
                    ),
                )
            )

    def test_recipiente_p13_classe_i(self):
        # 4 cilindros P-13 = 4 * 0.031 = 0.124 m³ <= 0.54 m³ -> Classe I
        dados = DadosCentralGLP(
            identificacao_projeto="Bateria Pequena P-13",
            tipo_consumidor=TipoConsumidor.COMERCIAL_RESTAURANTE,
            tipo_recipiente=TipoRecipiente.P_13,
            recipientes_em_servico=2,
            recipientes_em_reserva=2,
            consumo_pico_kg_h=Fraction(6, 10), # 0.60 kg/h <= 2 * 0.35 = 0.70 kg/h
            afastamentos=DadosAfastamentosReais(
                distancia_aberturas_m=Fraction(2, 1), # Req: 1.5m
                distancia_divisa_lote_m=Fraction(2, 1), # Req: 1.5m
                distancia_fontes_ignicao_m=Fraction(4, 1), # Req: 3.0m
                distancia_ralos_depressoes_m=Fraction(2, 1), # Req: 1.5m
            ),
        )
        res = dimensionar_central_glp(dados)
        self.assertEqual(res.classe_central, ClasseCentral.CLASSE_I)
        self.assertEqual(res.extintores_minimos_qtd, 1)
        self.assertTrue(res.conformidade_geral)

    def test_tanque_e1000_classe_iii(self):
        # 1x E-1000 = 2.4 m³ (Classe III: 2.16 < V <= 5.40 m³)
        dados = DadosCentralGLP(
            identificacao_projeto="Tanque E-1000 Padaria",
            tipo_consumidor=TipoConsumidor.COMERCIAL_RESTAURANTE,
            tipo_recipiente=TipoRecipiente.E_1000,
            recipientes_em_servico=1,
            recipientes_em_reserva=0,
            consumo_pico_kg_h=Fraction(15, 1), # <= 20 kg/h
            afastamentos=DadosAfastamentosReais(
                distancia_aberturas_m=Fraction(7, 1), # Req: 6.0m
                distancia_divisa_lote_m=Fraction(7, 1), # Req: 6.0m
                distancia_fontes_ignicao_m=Fraction(7, 1), # Req: 6.0m
                distancia_ralos_depressoes_m=Fraction(4, 1), # Req: 3.0m
            ),
        )
        res = dimensionar_central_glp(dados)
        self.assertEqual(res.classe_central, ClasseCentral.CLASSE_III)
        self.assertEqual(res.extintores_capacidade_min, "40-B:C")
        self.assertTrue(res.conformidade_geral)



if __name__ == "__main__":
    unittest.main()
