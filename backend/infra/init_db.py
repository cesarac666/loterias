import csv
import json
import sqlite3
from itertools import combinations
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DB_DIR = ROOT_DIR / 'database'
DB_PATH = DB_DIR / 'lotofacil.db'
LOTOFACIL_CSV = ROOT_DIR / 'ultimos500_lotofacil_05062023.csv'
DIA_DA_SORTE_CSV = ROOT_DIR / 'imports/notebooks/Dia_Da_Sorte.csv'


def _to_int(value: str) -> int:
    return int(value.strip())


def _compute_qdls(bolas):
    semanas = ((1, 7), (8, 14), (15, 21), (22, 28), (29, 31))
    return [sum(1 for bola in bolas if inicio <= bola <= fim) for inicio, fim in semanas]


def _compute_digit_stats(bolas):
    unidades = {str(i): 0 for i in range(10)}
    dezenas = {str(i): 0 for i in range(4)}
    for bola in bolas:
        unidades[str(bola % 10)] += 1
        dezenas[str(bola // 10)] += 1
    return {"units": unidades, "tens": dezenas}


def _to_coord(numero: int) -> tuple[int, int]:
    row = (numero - 1) // 7
    col = (numero - 1) % 7
    return row, col


def _count_isolated(bolas):
    coords = {numero: _to_coord(numero) for numero in bolas}
    isolados = 0
    for numero, (row, col) in coords.items():
        tem_vizinho = False
        for outro, (orow, ocol) in coords.items():
            if outro == numero:
                continue
            if abs(row - orow) <= 1 and abs(col - ocol) <= 1:
                tem_vizinho = True
                break
        if not tem_vizinho:
            isolados += 1
    return isolados


def _max_consecutive_run(bolas):
    ordenadas = sorted(bolas)
    if not ordenadas:
        return 0
    max_run = 1
    atual = 1
    for anterior, atual_val in zip(ordenadas, ordenadas[1:]):
        if atual_val == anterior + 1:
            atual += 1
        else:
            max_run = max(max_run, atual)
            atual = 1
    return max(max_run, atual)


def _max_jump(bolas):
    if len(bolas) < 2:
        return 0
    ordenadas = sorted(bolas)
    return max(b - a for a, b in zip(ordenadas, ordenadas[1:]))


def _load_lotofacil(cur: sqlite3.Cursor) -> None:
    cur.execute('DROP TABLE IF EXISTS results')
    cur.execute('''
        CREATE TABLE results (
            concurso INTEGER PRIMARY KEY,
            data TEXT NOT NULL,
            n1 INTEGER NOT NULL, n2 INTEGER NOT NULL, n3 INTEGER NOT NULL,
            n4 INTEGER NOT NULL, n5 INTEGER NOT NULL, n6 INTEGER NOT NULL,
            n7 INTEGER NOT NULL, n8 INTEGER NOT NULL, n9 INTEGER NOT NULL,
            n10 INTEGER NOT NULL, n11 INTEGER NOT NULL, n12 INTEGER NOT NULL,
            n13 INTEGER NOT NULL, n14 INTEGER NOT NULL, n15 INTEGER NOT NULL,
            ganhador INTEGER NOT NULL
        )
    ''')
    with LOTOFACIL_CSV.open(newline='') as f:
        reader = csv.reader(f)
        next(reader, None)
        rows = [
            [
                _to_int(row[0]),
                row[1].strip(),
                *(_to_int(n) for n in row[2:17]),
                _to_int(row[17]),
            ]
            for row in reader
            if row
        ]
    cur.executemany(
        'INSERT OR REPLACE INTO results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        rows,
    )


def _load_dia_da_sorte(cur: sqlite3.Cursor):
    cur.execute('DROP TABLE IF EXISTS dia_da_sorte_results')
    cur.execute('''
        CREATE TABLE dia_da_sorte_results (
            concurso INTEGER PRIMARY KEY,
            data_sorteio TEXT NOT NULL,
            bola1 INTEGER NOT NULL, bola2 INTEGER NOT NULL, bola3 INTEGER NOT NULL,
            bola4 INTEGER NOT NULL, bola5 INTEGER NOT NULL, bola6 INTEGER NOT NULL,
            bola7 INTEGER NOT NULL,
            mes_da_sorte INTEGER NOT NULL,
            ganhadores_7_acertos INTEGER NOT NULL,
            pares INTEGER NOT NULL,
            impares INTEGER NOT NULL,
            nah_n INTEGER,
            nah_a INTEGER,
            nah_h INTEGER,
            max_consec INTEGER NOT NULL,
            maior_salto INTEGER NOT NULL,
            isoladas INTEGER NOT NULL,
            qdls TEXT NOT NULL,
            digit_stats TEXT NOT NULL
        )
    ''')
    registros = []
    with DIA_DA_SORTE_CSV.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader, None)
        for row in reader:
            if not row:
                continue
            bolas = [_to_int(value) for value in row[2:9]]
            pares = sum(1 for value in bolas if value % 2 == 0)
            registros.append({
                'concurso': _to_int(row[0]),
                'data': row[1].strip(),
                'bolas': bolas,
                'mes': _to_int(row[9]),
                'ganhadores': _to_int(row[10]),
                'pares': pares,
                'impares': len(bolas) - pares,
                'max_consec': _max_consecutive_run(bolas),
                'maior_salto': _max_jump(bolas),
                'isoladas': _count_isolated(bolas),
                'qdls': _compute_qdls(bolas),
                'digit_stats': _compute_digit_stats(bolas),
            })

    for idx, registro in enumerate(registros):
        if idx < 2:
            registro['nah'] = (None, None, None)
            continue
        atual = set(registros[idx]['bolas'])
        anterior = set(registros[idx - 1]['bolas'])
        anterior2 = set(registros[idx - 2]['bolas'])
        N = atual - anterior
        A = (atual & anterior) - anterior2
        H = atual & anterior & anterior2
        registro['nah'] = (len(N), len(A), len(H))

    rows = []
    for registro in registros:
        n_val, a_val, h_val = registro['nah']
        rows.append([
            registro['concurso'],
            registro['data'],
            *registro['bolas'],
            registro['mes'],
            registro['ganhadores'],
            registro['pares'],
            registro['impares'],
            n_val,
            a_val,
            h_val,
            registro['max_consec'],
            registro['maior_salto'],
            registro['isoladas'],
            json.dumps(registro['qdls']),
            json.dumps(registro['digit_stats']),
        ])

    cur.executemany(
        'INSERT OR REPLACE INTO dia_da_sorte_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        rows,
    )
    return registros


def _load_dia_da_sorte_bets(cur: sqlite3.Cursor, registros) -> None:
    cur.execute('DROP TABLE IF EXISTS dia_da_sorte_bets')
    cur.execute('''
        CREATE TABLE dia_da_sorte_bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            d1 INTEGER NOT NULL,
            d2 INTEGER NOT NULL,
            d3 INTEGER NOT NULL,
            d4 INTEGER NOT NULL,
            d5 INTEGER NOT NULL,
            d6 INTEGER NOT NULL,
            d7 INTEGER NOT NULL,
            pares INTEGER NOT NULL,
            impares INTEGER NOT NULL,
            max_consec INTEGER NOT NULL,
            maior_salto INTEGER NOT NULL,
            isoladas INTEGER NOT NULL,
            nah_n INTEGER,
            nah_a INTEGER,
            nah_h INTEGER,
            qdls_s1 INTEGER NOT NULL,
            qdls_s2 INTEGER NOT NULL,
            qdls_s3 INTEGER NOT NULL,
            qdls_s4 INTEGER NOT NULL,
            qdls_s5 INTEGER NOT NULL,
            unit_0 INTEGER NOT NULL,
            unit_1 INTEGER NOT NULL,
            unit_2 INTEGER NOT NULL,
            unit_3 INTEGER NOT NULL,
            unit_4 INTEGER NOT NULL,
            unit_5 INTEGER NOT NULL,
            unit_6 INTEGER NOT NULL,
            unit_7 INTEGER NOT NULL,
            unit_8 INTEGER NOT NULL,
            unit_9 INTEGER NOT NULL,
            ten_0 INTEGER NOT NULL,
            ten_1 INTEGER NOT NULL,
            ten_2 INTEGER NOT NULL,
            ten_3 INTEGER NOT NULL
        )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_dia_bets_pares ON dia_da_sorte_bets(pares)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_dia_bets_impares ON dia_da_sorte_bets(impares)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_dia_bets_isoladas ON dia_da_sorte_bets(isoladas)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_dia_bets_maxconsec ON dia_da_sorte_bets(max_consec)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_dia_bets_maiorsalto ON dia_da_sorte_bets(maior_salto)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_dia_bets_nahn ON dia_da_sorte_bets(nah_n)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_dia_bets_naha ON dia_da_sorte_bets(nah_a)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_dia_bets_nahh ON dia_da_sorte_bets(nah_h)')

    ultimo = set(registros[-1]['bolas']) if registros else None
    penultimo = set(registros[-2]['bolas']) if len(registros) >= 2 else None

    insert_sql = '''
        INSERT INTO dia_da_sorte_bets (
            d1, d2, d3, d4, d5, d6, d7,
            pares, impares, max_consec, maior_salto, isoladas,
            nah_n, nah_a, nah_h,
            qdls_s1, qdls_s2, qdls_s3, qdls_s4, qdls_s5,
            unit_0, unit_1, unit_2, unit_3, unit_4, unit_5, unit_6, unit_7, unit_8, unit_9,
            ten_0, ten_1, ten_2, ten_3
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?
        )
    '''

    batch = []
    for combo in combinations(range(1, 32), 7):
        bolas = list(combo)
        pares = sum(1 for value in bolas if value % 2 == 0)
        impares = len(bolas) - pares
        max_consec = _max_consecutive_run(bolas)
        maior_salto = _max_jump(bolas)
        isoladas = _count_isolated(bolas)
        qdls = _compute_qdls(bolas)
        digit_stats = _compute_digit_stats(bolas)
        units_counts = [digit_stats['units'][str(i)] for i in range(10)]
        tens_counts = [digit_stats['tens'][str(i)] for i in range(4)]

        if ultimo:
            dezenas_set = set(bolas)
            nah_n = len(dezenas_set - ultimo)
            if penultimo:
                nah_a = len((dezenas_set & ultimo) - penultimo)
                nah_h = len(dezenas_set & ultimo & penultimo)
            else:
                nah_a = len(dezenas_set & ultimo)
                nah_h = 0
        else:
            nah_n = nah_a = nah_h = None

        batch.append([
            *bolas,
            pares,
            impares,
            max_consec,
            maior_salto,
            isoladas,
            nah_n,
            nah_a,
            nah_h,
            *qdls,
            *units_counts,
            *tens_counts,
        ])

        if len(batch) >= 5000:
            cur.executemany(insert_sql, batch)
            batch.clear()

    if batch:
        cur.executemany(insert_sql, batch)


def main() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _load_lotofacil(cur)
        registros = _load_dia_da_sorte(cur)
        _load_dia_da_sorte_bets(cur, registros)
        conn.commit()


if __name__ == '__main__':
    main()

