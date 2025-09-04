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
    tres_por_linha = request.args.get('tresPorLinha', '').lower() in ('1', 'true', 'on')
    concurso_limite = request.args.get('concursoLimite', type=int)
    pares = {int(p) for p in pares_param.split(',') if p}
    impares = {int(i) for i in impares_param.split(',') if i}

    conn = get_connection()
    cur = conn.execute(
        'SELECT concurso, data, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, ganhador '
        'FROM results'
    )
    rows = cur.fetchall()
    conn.close()

    from filters import FiltroDezenasParesImpares, FiltroTresPorLinha, FiltroConcursoLimite
    filtro_paridade = FiltroDezenasParesImpares(pares, impares, ativo=bool(pares or impares))
    filtro_tres = FiltroTresPorLinha(ativo=tres_por_linha)
    filtro_limite = FiltroConcursoLimite(concurso_limite, ativo=concurso_limite is not None)
    rows = filtro_paridade.apply(rows)
    rows = filtro_tres.apply(rows)
    rows = filtro_limite.apply(rows)

    total = len(rows)
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
    return jsonify({'total': total, 'results': results[:10]})

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == '__main__':
    app.run()
