from flask import Flask, jsonify, request
import sqlite3
import csv
from pathlib import Path

app = Flask(__name__)
DB_PATH = Path(__file__).with_name('lotofacil.db')

def get_connection():
    """Create a read-only connection to the SQLite database.

    Returns None if the database file is missing, logging the error for
    diagnostic purposes.
    """
    try:
        conn = sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError as exc:
        app.logger.error('Failed to connect to database %s: %s', DB_PATH, exc)
        return None


def classify_pattern(lines):
    counts = {c: lines.count(c) for c in set(lines)}
    if all(c == 3 for c in lines):
        return '3 por linha'
    if counts.get(3, 0) == 3 and counts.get(2, 0) == 1 and counts.get(4, 0) == 1:
        return 'quase 3 por linha'
    if 5 in lines:
        return '1 linha completa'
    return 'outro'


def classify_pattern(lines):
    counts = {c: lines.count(c) for c in set(lines)}
    if all(c == 3 for c in lines):
        return '3 por linha'
    if counts.get(3, 0) == 3 and counts.get(2, 0) == 1 and counts.get(4, 0) == 1:
        return 'quase 3 por linha'
    if 5 in lines:
        return '1 linha completa'
    return 'outro'


def classify_pattern(lines):
    counts = {c: lines.count(c) for c in set(lines)}
    if all(c == 3 for c in lines):
        return '3 por linha'
    if counts.get(3, 0) == 3 and counts.get(2, 0) == 1 and counts.get(4, 0) == 1:
        return 'quase 3 por linha'
    if 5 in lines:
        return '1 linha completa'
    return 'outro'


def classify_pattern(lines):
    counts = {c: lines.count(c) for c in set(lines)}
    if all(c == 3 for c in lines):
        return '3 por linha'
    if counts.get(3, 0) == 3 and counts.get(2, 0) == 1 and counts.get(4, 0) == 1:
        return 'quase 3 por linha'
    if 5 in lines:
        return '1 linha completa'
    return 'outro'


def classify_pattern(lines):
    counts = {c: lines.count(c) for c in set(lines)}
    if all(c == 3 for c in lines):
        return '3 por linha'
    if counts.get(3, 0) == 3 and counts.get(2, 0) == 1 and counts.get(4, 0) == 1:
        return 'quase 3 por linha'
    if 5 in lines:
        return '1 linha completa'
    return 'outro'

@app.route('/api/results')
def list_results():
    def _parse_int_list(values):
        nums = set()
        for v in values:
            for part in v.replace(';', ',').split(','):
                part = part.strip()
                if part:
                    try:
                        nums.add(int(part))
                    except ValueError:
                        continue
        return nums

    pares_param = request.args.get('pares', '')
    impares_param = request.args.get('impares', '')
    pares = _parse_int_list(request.args.getlist('pares') or [pares_param])
    impares = _parse_int_list(request.args.getlist('impares') or [impares_param])
    concurso_limite = request.args.get('concursoLimite', type=int)
    padrao_linha = request.args.get('padraoLinha')

    from filters import FiltroDezenasParesImpares, FiltroConcursoLimite
    filtro_paridade = FiltroDezenasParesImpares(pares, impares, ativo=bool(pares or impares))
    filtro_limite = FiltroConcursoLimite(concurso_limite, ativo=concurso_limite is not None)

    conn = get_connection()
    if conn is None:
        app.logger.warning('lotofacil.db not found; returning empty results')
        return jsonify({'error': 'lotofacil.db not found', 'total': 0, 'results': []}), 500
    cur = conn.execute(
        'SELECT concurso, data, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, ganhador '
        'FROM results'
    )
    rows = cur.fetchall()
    conn.close()

    rows = filtro_paridade.apply(rows)
    rows = filtro_limite.apply(rows)

    total = len(rows)
    results = []
    for r in rows:
        dezenas = [r[f'n{i}'] for i in range(1, 16)]
        qtd_pares = sum(1 for d in dezenas if d % 2 == 0)
        qtd_impares = len(dezenas) - qtd_pares
        lines = [0]*5
        for d in dezenas:
            lines[(d-1)//5] += 1
        padrao = classify_pattern(lines)

        if padrao_linha and padrao != padrao_linha:
            continue

        results.append({
            'concurso': r['concurso'],
            'data': r['data'],
            'dezenas': dezenas,
            'ganhador': r['ganhador'],
            'qtdPares': qtd_pares,
            'qtdImpares': qtd_impares,
            'padraoLinha': padrao,
        })
    results.sort(key=lambda x: x['concurso'], reverse=True)
    return jsonify({'total': total, 'results': results[:500]})


@app.route('/api/apostas')
def list_apostas():
    def _parse_int_list(values):
        nums = set()
        for v in values:
            for part in v.replace(';', ',').split(','):
                part = part.strip()
                if part:
                    try:
                        nums.add(int(part))
                    except ValueError:
                        continue
        return nums

    pares_param = request.args.get('pares', '')
    impares_param = request.args.get('impares', '')
    pares = _parse_int_list(request.args.getlist('pares') or [pares_param])
    impares = _parse_int_list(request.args.getlist('impares') or [impares_param])
    concurso_limite = request.args.get('concursoLimite', type=int)

    csv_path = Path(__file__).resolve().parent.parent / 'todasTresPorLinha.csv'
    with csv_path.open(newline='') as f:
        reader = csv.DictReader(f)
        rows = []
        for idx, row in enumerate(reader, start=1):
            data_row = {f'n{i}': int(row[f'B{i}']) for i in range(1, 16)}
            data_row['concurso'] = idx
            data_row['data'] = ''
            data_row['ganhador'] = 0
            rows.append(data_row)

    from filters import FiltroDezenasParesImpares, FiltroConcursoLimite
    filtro_paridade = FiltroDezenasParesImpares(pares, impares, ativo=bool(pares or impares))
    filtro_limite = FiltroConcursoLimite(concurso_limite, ativo=concurso_limite is not None)
    rows = filtro_paridade.apply(rows)
    rows = filtro_limite.apply(rows)

    total = len(rows)
    results = []
    for r in rows:
        dezenas = [r[f'n{i}'] for i in range(1, 16)]
        qtd_pares = sum(1 for d in dezenas if d % 2 == 0)
        qtd_impares = len(dezenas) - qtd_pares
        lines = [0]*5
        for d in dezenas:
            lines[(d-1)//5] += 1
        padrao = classify_pattern(lines)
        results.append({
            'concurso': r['concurso'],
            'data': r['data'],
            'dezenas': dezenas,
            'ganhador': r['ganhador'],
            'qtdPares': qtd_pares,
            'qtdImpares': qtd_impares,
            'padraoLinha': padrao,
        })
    results.sort(key=lambda x: x['concurso'])
    return jsonify({'total': total, 'results': results[:10]})

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == '__main__':
    app.run()
