"""Testes unitários para exportadores de memorial descritivo, CSV e ZIP."""

import os
import tempfile
import unittest
import zipfile
from fractions import Fraction

from central_glp_nbr13523.exporters import (
    _fmt,
    _sanitizar_campo_csv,
    gerar_csv_afastamentos,
    gerar_pacote_zip_central_glp,
    gerar_relatorio_central_glp_texto,
)
from central_glp_nbr13523.models import (
    ClasseCentral,
    ResultadoCentralGLP,
    ResultadoItemAfastamento,
    ResultadoVaporizacao,
    TipoConsumidor,
    TipoRecipiente,
)


class TestExporters(unittest.TestCase):
    def setUp(self):
        res_item = ResultadoItemAfastamento(
            item="Aberturas de Edificações",
            distancia_exigida_m=Fraction(3, 1),
            distancia_real_m=Fraction(7, 2),  # 3.5m
            conforme=True,
            observacao="Atende ao afastamento",
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
        self.res = ResultadoCentralGLP(
            identificacao_projeto="Edifício Teste Exporter",
            tipo_consumidor=TipoConsumidor.RESIDENCIAL_COLETIVO,
            tipo_recipiente=TipoRecipiente.P_45,
            classe_central=ClasseCentral.CLASSE_II,
            volume_total_m3=Fraction(162, 125),  # 1.296 m³
            capacidade_massa_total_kg=540,
            total_recipientes=12,
            configuracao_bateria="Bateria Dupla (6 em serviço + 6 reserva) - P_45",
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
            alertas_tecnicos=[],
        )

    def test_fmt_fracao(self):
        self.assertEqual(_fmt(Fraction(5, 1), 2), "5.0")
        self.assertEqual(_fmt(Fraction(7, 2), 2), "3.50")
        self.assertEqual(_fmt(Fraction(1, 3), 2), "0.33")

    def test_sanitizar_campo_csv(self):
        self.assertEqual(_sanitizar_campo_csv("=1+1"), "'=1+1")
        self.assertEqual(_sanitizar_campo_csv("+SOMA()"), "'+SOMA()")
        self.assertEqual(_sanitizar_campo_csv("-123"), "'-123")
        self.assertEqual(_sanitizar_campo_csv("@cmd"), "'@cmd")
        self.assertEqual(_sanitizar_campo_csv("\ttab"), "'\ttab")
        self.assertEqual(_sanitizar_campo_csv("Normal"), "Normal")

    def test_gerar_relatorio_central_glp_texto(self):
        texto = gerar_relatorio_central_glp_texto(self.res)
        self.assertIn("LOFRANO TECNOLOGIA", texto)
        self.assertIn("NBR 13523:2019", texto)
        self.assertIn("Edifício Teste Exporter", texto)
        self.assertIn("CLASSE_II", texto)
        self.assertIn("540 kg", texto)
        self.assertIn("CONFORME", texto)

    def test_gerar_csv_afastamentos(self):
        csv_str = gerar_csv_afastamentos(self.res)
        self.assertIn("item_afastamento;distancia_exigida_m;distancia_real_m;conforme;observacao", csv_str)
        self.assertIn("Aberturas de Edificações", csv_str)
        self.assertIn("SIM", csv_str)

    def test_gerar_pacote_zip_determinismo_e_exclusividade(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho_zip = os.path.join(tmpdir, "pacote_teste.zip")
            gerar_pacote_zip_central_glp(self.res, caminho_zip, svg_conteudo="<svg></svg>")
            self.assertTrue(os.path.exists(caminho_zip))

            # Verifica integridade do zip e data fixa 2026-01-01
            with zipfile.ZipFile(caminho_zip, "r") as zf:
                nomes = zf.namelist()
                self.assertIn("memorial_central_glp.txt", nomes)
                self.assertIn("dados_central_glp.json", nomes)
                self.assertIn("afastamentos_seguranca.csv", nomes)
                self.assertIn("painel_central_glp.svg", nomes)

                info = zf.getinfo("memorial_central_glp.txt")
                self.assertEqual(info.date_time, (2026, 1, 1, 0, 0, 0))

            # Teste de proteção O_EXCL (falha ao tentar sobrescrever arquivo existente)
            with self.assertRaises(FileExistsError):
                gerar_pacote_zip_central_glp(self.res, caminho_zip)


if __name__ == "__main__":
    unittest.main()
