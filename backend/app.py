from flask import Flask, jsonify, request
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB_PATH = Path(__file__).with_name('lotofacil.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/results')
def list_results():
    pares_param = request.args.get('pares', '')
    impares_param = request.args.get('impares', '')
    pares = {int(p) for p in pares_param.split(',') if p}
    impares = {int(i) for i in impares_param.split(',') if i}

    conn = get_connection()
    cur = conn.execute(
        'SELECT concurso, data, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, ganhador '
        'FROM results'
    )
    rows = cur.fetchall()
    conn.close()

    from filters import FiltroDezenasParesImpares
    filtro = FiltroDezenasParesImpares(pares, impares, ativo=bool(pares or impares))
    rows = filtro.apply(rows)

    results = []
    for r in rows:
        dezenas = [r[f'n{i}'] for i in range(1, 16)]
        results.append({
            'concurso': r['concurso'],
            'data': r['data'],
            'dezenas': dezenas,
            'ganhador': r['ganhador'],
        })
    results.sort(key=lambda x: x['concurso'], reverse=True)
    return jsonify(results[:10])

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == '__main__':
    app.run()
