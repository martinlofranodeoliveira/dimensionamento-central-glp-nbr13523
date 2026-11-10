"""Testes unitários para a CLI central-glp-nbr13523."""

import io
import os
import sys
import tempfile
import unittest

from central_glp_nbr13523 import __version__
from central_glp_nbr13523.cli import main


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.held_stdout = io.StringIO()
        self.held_stderr = io.StringIO()
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = self.held_stdout
        sys.stderr = self.held_stderr

    def tearDown(self):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

    def test_cli_ajuda(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["--ajuda"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("Dimensionamento e Auditoria de Centrais de GLP", self.held_stdout.getvalue())

    def test_cli_versao(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["--versao"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn(__version__, self.held_stdout.getvalue())

    def test_cli_catalogo(self):
        codigo = main(["catalogo"])
        self.assertEqual(codigo, 0)
        saida = self.held_stdout.getvalue()
        self.assertIn("PARÂMETROS NORMATIVOS DA ABNT NBR 13523:2019", saida)
        self.assertIn("P-45", saida)
        self.assertIn("Classe I", saida)

    def test_cli_gerar_exemplo_stdout(self):
        codigo = main(["gerar-exemplo"])
        self.assertEqual(codigo, 0)
        saida = self.held_stdout.getvalue()
        self.assertIn("identificacao_projeto", saida)
        self.assertIn("tipo_recipiente", saida)

    def test_cli_gerar_exemplo_arquivo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            arq = os.path.join(tmpdir, "exemplo_gerado.json")
            codigo = main(["gerar-exemplo", "-o", arq])
            self.assertEqual(codigo, 0)
            self.assertTrue(os.path.exists(arq))

    def test_cli_arquivo_inexistente(self):
        codigo = main(["calcular", "arquivo_que_nao_existe.json"])
        self.assertEqual(codigo, 1)
        self.assertIn("Erro ao ler arquivo", self.held_stderr.getvalue())

    def test_cli_calcular_sucesso(self):
        raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        exemplo = os.path.join(raiz, "examples", "central_edificio_residencial_p45.json")
        codigo = main(["calcular", exemplo])
        self.assertEqual(codigo, 0)
        saida = self.held_stdout.getvalue()
        self.assertIn("LOFRANO TECNOLOGIA", saida)
        self.assertIn("MEMORIAL DE DIMENSIONAMENTO DE CENTRAL DE GLP", saida)
        self.assertIn("CONFORME", saida)

    def test_cli_calcular_formatos(self):
        raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        exemplo = os.path.join(raiz, "examples", "central_edificio_residencial_p45.json")

        for fmt in ["json", "csv", "svg"]:
            self.held_stdout = io.StringIO()
            sys.stdout = self.held_stdout
            codigo = main(["calcular", exemplo, "-f", fmt])
            self.assertEqual(codigo, 0)
            saida = self.held_stdout.getvalue()
            if fmt == "json":
                self.assertIn('"norma": "ABNT NBR 13523:2019"', saida)
            elif fmt == "csv":
                self.assertIn("item_afastamento;", saida)
            elif fmt == "svg":
                self.assertIn("<svg", saida)

    def test_cli_calcular_pacote_zip(self):
        raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        exemplo = os.path.join(raiz, "examples", "central_edificio_residencial_p45.json")
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho_zip = os.path.join(tmpdir, "pacote_cli.zip")
            codigo = main(["calcular", exemplo, "--pacote-zip", caminho_zip])
            self.assertEqual(codigo, 0)
            self.assertTrue(os.path.exists(caminho_zip))


if __name__ == "__main__":
    unittest.main()
