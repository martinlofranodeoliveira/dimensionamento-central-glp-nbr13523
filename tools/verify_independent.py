#!/usr/bin/env python3
"""Auditor independente em SQLite em memória para Centrais de GLP (ABNT NBR 13523:2019).

Este script é 100% desacoplado do código de produção de 'src/central_glp_nbr13523' e NÃO
importa nenhum módulo do pacote. Utiliza exclusivamente a biblioteca padrão do Python
e SQLite em memória para verificar a conformidade regulamentar dos cenários em 'examples/'.
"""

import glob
import json
import os
import sqlite3
import sys
from fractions import Fraction


def para_fracao(val) -> Fraction:
    return Fraction(str(val))


def criar_banco_normativo() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # 1. Tabela de limites de volume das classes
    cursor.execute("""
        CREATE TABLE classes_normativas (
            classe TEXT PRIMARY KEY,
            vol_max_num INTEGER,
            vol_max_den INTEGER
        );
    """)
    limites = [
        ("CLASSE_I", 54, 100),
        ("CLASSE_II", 216, 100),
        ("CLASSE_III", 540, 100),
        ("CLASSE_IV", 1620, 100),
        ("CLASSE_V", 3240, 100),
        ("CLASSE_VI", 6480, 100),
    ]
    cursor.executemany("INSERT INTO classes_normativas VALUES (?, ?, ?);", limites)

    # 2. Tabela de recipientes oficiais
    cursor.execute("""
        CREATE TABLE catalogo_recipientes (
            tipo TEXT PRIMARY KEY,
            massa_kg INTEGER,
            vol_num INTEGER,
            vol_den INTEGER,
            vap_num INTEGER,
            vap_den INTEGER
        );
    """)
    recipientes = [
        ("P_13", 13, 31, 1000, 7, 20),
        ("P_20", 20, 48, 1000, 1, 2),
        ("P_45", 45, 108, 1000, 1, 1),
        ("P_90", 90, 216, 1000, 2, 1),
        ("P_190", 190, 456, 1000, 7, 2),
        ("E_500", 500, 12, 10, 12, 1),
        ("E_1000", 1000, 24, 10, 20, 1),
        ("E_2000", 2000, 48, 10, 35, 1),
        ("E_4000", 4000, 96, 10, 60, 1),
    ]
    cursor.executemany("INSERT INTO catalogo_recipientes VALUES (?, ?, ?, ?, ?, ?);", recipientes)

    # 3. Tabela de afastamentos de segurança (NBR 13523)
    cursor.execute("""
        CREATE TABLE afastamentos_normativos (
            classe TEXT PRIMARY KEY,
            aberturas_num INTEGER, aberturas_den INTEGER,
            divisa_num INTEGER, divisa_den INTEGER,
            ignicao_num INTEGER, ignicao_den INTEGER,
            ralos_num INTEGER, ralos_den INTEGER,
            tanques_num INTEGER, tanques_den INTEGER,
            ext_qtd INTEGER,
            ext_cap TEXT,
            resfriamento INTEGER
        );
    """)
    afastamentos = [
        ("CLASSE_I", 3, 2, 3, 2, 3, 1, 3, 2, 6, 1, 1, "20-B:C", 0),
        ("CLASSE_II", 3, 1, 3, 1, 3, 1, 3, 2, 6, 1, 2, "20-B:C", 0),
        ("CLASSE_III", 6, 1, 6, 1, 6, 1, 3, 1, 10, 1, 2, "40-B:C", 0),
        ("CLASSE_IV", 15, 2, 15, 2, 15, 2, 3, 1, 10, 1, 2, "80-B:C", 1),
        ("CLASSE_V", 10, 1, 10, 1, 10, 1, 3, 1, 15, 1, 3, "80-B:C", 1),
        ("CLASSE_VI", 15, 1, 15, 1, 15, 1, 3, 1, 15, 1, 3, "80-B:C", 1),
    ]
    cursor.executemany("INSERT INTO afastamentos_normativos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", afastamentos)

    conn.commit()
    return conn


def auditar_cenario(caminho_json: str, conn: sqlite3.Connection) -> bool:
    nome_arq = os.path.basename(caminho_json)
    print(f"\n[AUDITORIA INDEPENDENTE] Verificando cenário: {nome_arq}")

    with open(caminho_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    tipo_rec = dados.get("tipo_recipiente", "P_45")
    rec_servico = int(dados.get("recipientes_em_servico", 1))
    rec_reserva = int(dados.get("recipientes_em_reserva", 0))
    total_rec = rec_servico + rec_reserva
    consumo_pico = para_fracao(dados.get("consumo_pico_kg_h", 1))

    cursor = conn.cursor()
    cursor.execute(
        "SELECT massa_kg, vol_num, vol_den, vap_num, vap_den FROM catalogo_recipientes WHERE tipo = ?;",
        (tipo_rec,)
    )
    row = cursor.fetchone()
    if not row:
        print(f"[FALHA] Tipo de recipiente desconhecido: {tipo_rec}", file=sys.stderr)
        return False

    massa_unit, vol_num, vol_den, vap_num, vap_den = row
    vol_unit = Fraction(vol_num, vol_den)
    vap_unit = Fraction(vap_num, vap_den)

    volume_total = vol_unit * total_rec
    massa_total = massa_unit * total_rec

    # Enquadramento de Classe
    cursor.execute("SELECT classe, vol_max_num, vol_max_den FROM classes_normativas ORDER BY vol_max_num * 1.0 / vol_max_den ASC;")
    classes_rows = cursor.fetchall()

    classe_encontrada = None
    for c_nome, c_num, c_den in classes_rows:
        if volume_total <= Fraction(c_num, c_den):
            classe_encontrada = c_nome
            break

    if not classe_encontrada:
        print(f"[FALHA] Volume total {volume_total} m³ excede Classe VI!", file=sys.stderr)
        return False

    print(f"  Enquadramento: {classe_encontrada} | Volume: {float(volume_total):.3f} m³ | Massa Total: {massa_total} kg")

    # Auditoria de Vaporização Natural
    cap_vap_total = vap_unit * rec_servico
    vap_ok = cap_vap_total >= consumo_pico
    print(
        f"  Vaporização Natural: Demanda={float(consumo_pico):.2f} kg/h | "
        f"Capacidade={float(cap_vap_total):.2f} kg/h [{ 'CONFORME' if vap_ok else 'INSUFICIENTE' }]"
    )
    if not vap_ok:
        return False

    # Auditoria de Afastamentos Normativos
    cursor.execute("SELECT * FROM afastamentos_normativos WHERE classe = ?;", (classe_encontrada,))
    afast_tab = cursor.fetchone()
    exig_aberturas = Fraction(afast_tab[1], afast_tab[2])
    exig_divisa = Fraction(afast_tab[3], afast_tab[4])
    exig_ignicao = Fraction(afast_tab[5], afast_tab[6])
    exig_ralos = Fraction(afast_tab[7], afast_tab[8])
    exig_tanques = Fraction(afast_tab[9], afast_tab[10])

    afast_dados = dados.get("afastamentos", {})
    real_aberturas = para_fracao(afast_dados.get("distancia_aberturas_m", 0))
    real_divisa = para_fracao(afast_dados.get("distancia_divisa_lote_m", 0))
    real_ignicao = para_fracao(afast_dados.get("distancia_fontes_ignicao_m", 0))
    real_ralos = para_fracao(afast_dados.get("distancia_ralos_depressoes_m", 0))
    real_tanques = para_fracao(afast_dados.get("distancia_tanques_inflamaveis_m", 999))

    muro_dados = dados.get("muro_protecao", {})
    possui_muro = bool(muro_dados.get("possui_muro", False))
    altura_muro = para_fracao(muro_dados.get("altura_m", 0))
    trrf_muro = int(muro_dados.get("trrf_min", 0))
    contorno_muro = para_fracao(muro_dados.get("distancia_pelo_contorno_m", 0))

    muro_valido = possui_muro and altura_muro >= Fraction(9, 5) and trrf_muro >= 120

    # 1. Aberturas
    ok_aberturas = real_aberturas >= exig_aberturas or (muro_valido and contorno_muro >= exig_aberturas)
    print(f"    - Aberturas: Req={float(exig_aberturas)}m | Real={float(real_aberturas)}m [{ 'CONFORME' if ok_aberturas else 'FALHA' }]")

    # 2. Divisa
    ok_divisa = real_divisa >= exig_divisa or (muro_valido and contorno_muro >= exig_divisa)
    print(f"    - Divisas de Lote: Req={float(exig_divisa)}m | Real={float(real_divisa)}m [{ 'CONFORME' if ok_divisa else 'FALHA' }]")

    # 3. Fontes de Ignição
    ok_ignicao = real_ignicao >= exig_ignicao
    print(f"    - Fontes de Ignição: Req={float(exig_ignicao)}m | Real={float(real_ignicao)}m [{ 'CONFORME' if ok_ignicao else 'FALHA' }]")

    # 4. Ralos e Depressões
    ok_ralos = real_ralos >= exig_ralos
    print(f"    - Ralos/Depressões: Req={float(exig_ralos)}m | Real={float(real_ralos)}m [{ 'CONFORME' if ok_ralos else 'FALHA' }]")

    # 5. Tanques Inflamáveis
    ok_tanques = real_tanques >= exig_tanques
    print(f"    - Tanques Inflamáveis: Req={float(exig_tanques)}m | Real={float(real_tanques)}m [{ 'CONFORME' if ok_tanques else 'FALHA' }]")

    cenario_conforme = ok_aberturas and ok_divisa and ok_ignicao and ok_ralos and ok_tanques and vap_ok
    if cenario_conforme:
        print(f"[OK] Cenário '{nome_arq}' 100% aprovado pela auditoria independente.")
        return True
    else:
        print(f"[FALHA] Cenário '{nome_arq}' possui inconformidades!", file=sys.stderr)
        return False


def main() -> int:
    print("=" * 80)
    print("   LOFRANO TECNOLOGIA - AUDITORIA INDEPENDENTE SQLITE (NBR 13523:2019)")
    print("=" * 80)

    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pasta_exemplos = os.path.join(raiz, "examples")
    arquivos = sorted(glob.glob(os.path.join(pasta_exemplos, "*.json")))

    if not arquivos:
        print(f"[ERRO] Nenhum arquivo JSON encontrado em '{pasta_exemplos}'!", file=sys.stderr)
        return 1

    conn = criar_banco_normativo()
    sucessos = 0
    total = len(arquivos)

    for arq in arquivos:
        if auditar_cenario(arq, conn):
            sucessos += 1

    conn.close()

    print("\n" + "=" * 80)
    print(f"Total de Cenários Auditados: {total}")
    print(f"Cenários Aprovados:          {sucessos}")
    taxa = (sucessos * 100) // total if total > 0 else 0
    print(f"Taxa de Conformidade:        {taxa}%")
    print("=" * 80)

    return 0 if sucessos == total else 1


if __name__ == "__main__":
    sys.exit(main())
