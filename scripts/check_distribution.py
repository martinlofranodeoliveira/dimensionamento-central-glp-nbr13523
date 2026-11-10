#!/usr/bin/env python3
"""Validação de integridade dos pacotes de distribuição sdist e wheel."""

import glob
import os
import sys
import tarfile
import zipfile


def verificar_distribuicao() -> int:
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dist_dir = os.path.join(raiz, "dist")

    sdists = glob.glob(os.path.join(dist_dir, "*.tar.gz"))
    wheels = glob.glob(os.path.join(dist_dir, "*.whl"))

    if not sdists:
        print("[ERRO] Nenhum arquivo .tar.gz encontrado em dist/", file=sys.stderr)
        return 1
    if not wheels:
        print("[ERRO] Nenhum arquivo .whl encontrado em dist/", file=sys.stderr)
        return 1

    sdist_path = sdists[0]
    print(f"Verificando sdist: {os.path.basename(sdist_path)}")
    with tarfile.open(sdist_path, "r:gz") as tar:
        membros = tar.getnames()
        print(f"  Total de arquivos no sdist: {len(membros)}")
        arquivos_chave = ["pyproject.toml", "LICENSE", "README.md"]
        for arq in arquivos_chave:
            encontrado = any(arq in m for m in membros)
            if not encontrado:
                print(f"[ERRO] Arquivo obrigatório '{arq}' não encontrado no sdist!", file=sys.stderr)
                return 1

    wheel_path = wheels[0]
    print(f"Verificando wheel: {os.path.basename(wheel_path)}")
    with zipfile.ZipFile(wheel_path, "r") as whl:
        membros = whl.namelist()
        print(f"  Total de arquivos no wheel: {len(membros)}")
        arquivos_chave_wheel = ["central_glp_nbr13523/__init__.py", "central_glp_nbr13523/py.typed"]
        for arq in arquivos_chave_wheel:
            if arq not in membros:
                print(f"[ERRO] Arquivo obrigatório '{arq}' não encontrado no wheel!", file=sys.stderr)
                return 1

    print("\nArtefatos de distribuição sdist e wheel validados com sucesso!")
    return 0


if __name__ == "__main__":
    sys.exit(verificar_distribuicao())
