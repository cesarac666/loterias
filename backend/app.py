from flask import Flask, jsonify, request
import sqlite3
import json 
import csv
import sys
import logging
import subprocess
import math
import random
import re
from collections import Counter, defaultdict
from logging.handlers import RotatingFileHandler
from typing import Optional
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from imports.update_diadesorte_results import update_results as update_dia_da_sorte_results
from imports.update_lotofacil_results import update_results as update_lotofacil_results

app = Flask(__name__)
DB_PATH = ROOT_DIR / 'database' / 'lotofacil.db'
LOG_PATH = BASE_DIR / 'app.log'
CHECKOUT_SCRIPT = ROOT_DIR / 'scripts' / 'dia_da_sorte_checkout.py'
LOTOFACIL_CHECKOUT_SCRIPT = ROOT_DIR / 'scripts' / 'lotofacil_checkout.py'
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

if not app.logger.handlers:
    handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=5, encoding='utf-8')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

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


def get_write_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError as exc:
        app.logger.error('Failed to open database %s: %s', DB_PATH, exc)
        return None


def _ensure_saved_bets_table(cur: sqlite3.Cursor) -> None:
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS dia_da_sorte_saved_bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concurso INTEGER NOT NULL,
            d1 INTEGER NOT NULL,
            d2 INTEGER NOT NULL,
            d3 INTEGER NOT NULL,
            d4 INTEGER NOT NULL,
            d5 INTEGER NOT NULL,
            d6 INTEGER NOT NULL,
            d7 INTEGER NOT NULL,
            acertos INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    cur.execute(
        '''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_bets_unique
        ON dia_da_sorte_saved_bets(concurso, d1, d2, d3, d4, d5, d6, d7)
        '''
    )
    cur.execute(
        '''
        CREATE INDEX IF NOT EXISTS idx_saved_bets_concurso
        ON dia_da_sorte_saved_bets(concurso)
        '''
    )


def _ensure_lotofacil_saved_bets_table(cur: sqlite3.Cursor) -> None:
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS lotofacil_saved_bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concurso INTEGER NOT NULL,
            n1 INTEGER NOT NULL, n2 INTEGER NOT NULL, n3 INTEGER NOT NULL,
            n4 INTEGER NOT NULL, n5 INTEGER NOT NULL, n6 INTEGER NOT NULL,
            n7 INTEGER NOT NULL, n8 INTEGER NOT NULL, n9 INTEGER NOT NULL,
            n10 INTEGER NOT NULL, n11 INTEGER NOT NULL, n12 INTEGER NOT NULL,
            n13 INTEGER NOT NULL, n14 INTEGER NOT NULL, n15 INTEGER NOT NULL,
            acertos INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            registrado_em TEXT
        )
        '''
    )
    cur.execute(
        '''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_lotofacil_saved_bets_unique
        ON lotofacil_saved_bets(concurso, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15)
        '''
    )
    cur.execute(
        '''
        CREATE INDEX IF NOT EXISTS idx_lotofacil_saved_bets_concurso
        ON lotofacil_saved_bets(concurso)
        '''
    )

    # Add column for older databases if missing.
    try:
        cols = [row[1] for row in cur.execute("PRAGMA table_info(lotofacil_saved_bets)").fetchall()]
    except Exception:
        cols = []
    if 'registrado_em' not in cols:
        cur.execute("ALTER TABLE lotofacil_saved_bets ADD COLUMN registrado_em TEXT")


UNIT_DIGITS = [str(i) for i in range(10)]
TEN_DIGITS = [str(i) for i in range(4)]


def _safe_json_loads(value, fallback):
    if value in (None, ''):
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _value_summary_from_list(values):
    filtered = [v for v in values if v is not None]
    if not filtered:
        return None
    counter = Counter(filtered)
    mode = max(counter.items(), key=lambda item: (item[1], item[0]))[0]
    return {'min': min(filtered), 'max': max(filtered), 'mode': mode}


def _classify_digit(avg: float, baseline: float) -> str:
    tolerance = 0.2
    if avg > baseline + tolerance:
        return 'quente'
    if avg < baseline - tolerance:
        return 'fria'
    return 'neutra'


def _compute_dia_da_sorte_summary(results: list[dict]) -> Optional[dict]:
    if not results:
        return None

    metrics = defaultdict(list)
    nah_metrics = {'n': [], 'a': [], 'h': []}
    qdls_values = [[] for _ in range(5)]
    units_values = {key: [] for key in UNIT_DIGITS}
    tens_values = {key: [] for key in TEN_DIGITS}
    unit_totals = {key: 0 for key in UNIT_DIGITS}
    ten_totals = {key: 0 for key in TEN_DIGITS}

    for item in results:
        metrics['pares'].append(item.get('pares'))
        metrics['impares'].append(item.get('impares'))
        metrics['maxConsec'].append(item.get('maxConsec'))
        metrics['maiorSalto'].append(item.get('maiorSalto'))
        metrics['isolatedCount'].append(item.get('isolatedCount'))
        metrics['ganhadores7'].append(item.get('ganhadores7Acertos'))

        nah_n = item.get('nahN')
        nah_a = item.get('nahA')
        nah_h = item.get('nahH')
        if nah_n is not None:
            nah_metrics['n'].append(nah_n)
        if nah_a is not None:
            nah_metrics['a'].append(nah_a)
        if nah_h is not None:
            nah_metrics['h'].append(nah_h)

        qdls = item.get('qdls') or []
        for idx, value in enumerate(qdls):
            if idx < len(qdls_values):
                qdls_values[idx].append(value)

        digit_stats = item.get('digitStats') or {}
        units = digit_stats.get('units') or {}
        tens = digit_stats.get('tens') or {}
        for key in UNIT_DIGITS:
            val = int(units.get(key, 0) or 0)
            units_values[key].append(val)
            unit_totals[key] += val
        for key in TEN_DIGITS:
            val = int(tens.get(key, 0) or 0)
            tens_values[key].append(val)
            ten_totals[key] += val

    total_records = len(results)
    total_units = sum(unit_totals.values())
    total_tens = sum(ten_totals.values())
    overall_units_avg = total_units / len(UNIT_DIGITS) / total_records if total_records else 0.0
    overall_tens_avg = total_tens / len(TEN_DIGITS) / total_records if total_records else 0.0

    digit_frequency_units = {
        key: {
            'total': unit_totals[key],
            'average': unit_totals[key] / total_records if total_records else 0.0,
            'profile': _classify_digit(
                unit_totals[key] / total_records if total_records else 0.0,
                overall_units_avg,
            ),
        }
        for key in UNIT_DIGITS
    }
    digit_frequency_tens = {
        key: {
            'total': ten_totals[key],
            'average': ten_totals[key] / total_records if total_records else 0.0,
            'profile': _classify_digit(
                ten_totals[key] / total_records if total_records else 0.0,
                overall_tens_avg,
            ),
        }
        for key in TEN_DIGITS
    }

    summary = {
        'pares': _value_summary_from_list(metrics['pares']),
        'impares': _value_summary_from_list(metrics['impares']),
        'maxConsec': _value_summary_from_list(metrics['maxConsec']),
        'maiorSalto': _value_summary_from_list(metrics['maiorSalto']),
        'isolatedCount': _value_summary_from_list(metrics['isolatedCount']),
        'ganhadores7': _value_summary_from_list(metrics['ganhadores7']),
        'nah': {
            'n': _value_summary_from_list(nah_metrics['n']),
            'a': _value_summary_from_list(nah_metrics['a']),
            'h': _value_summary_from_list(nah_metrics['h']),
        },
        'qdls': [_value_summary_from_list(values) for values in qdls_values],
        'digitStats': {
            'units': {key: _value_summary_from_list(units_values[key]) for key in UNIT_DIGITS},
            'tens': {key: _value_summary_from_list(tens_values[key]) for key in TEN_DIGITS},
        },
        'digitFrequency': {
            'units': digit_frequency_units,
            'tens': digit_frequency_tens,
            'overallUnitsAverage': overall_units_avg,
            'overallTensAverage': overall_tens_avg,
        },
    }
    return summary


def _fetch_dia_da_sorte_results(cur: sqlite3.Cursor) -> list[dict]:
    rows = cur.execute(
        '''
            SELECT
                concurso,
                data_sorteio,
                bola1,
                bola2,
                bola3,
                bola4,
                bola5,
                bola6,
                bola7,
                mes_da_sorte,
                ganhadores_7_acertos,
                pares,
                impares,
                nah_n,
                nah_a,
                nah_h,
                max_consec,
                maior_salto,
                isoladas,
                qdls,
                digit_stats
            FROM dia_da_sorte_results
            ORDER BY concurso DESC
        '''
    ).fetchall()

    results = []
    for row in rows:
        results.append({
            'concurso': row['concurso'],
            'dataSorteio': row['data_sorteio'],
            'bolas': [
                row['bola1'],
                row['bola2'],
                row['bola3'],
                row['bola4'],
                row['bola5'],
                row['bola6'],
                row['bola7'],
            ],
            'mesDaSorte': row['mes_da_sorte'],
            'ganhadores7Acertos': row['ganhadores_7_acertos'],
            'pares': row['pares'],
            'impares': row['impares'],
            'nahN': row['nah_n'],
            'nahA': row['nah_a'],
            'nahH': row['nah_h'],
            'maxConsec': row['max_consec'],
            'maiorSalto': row['maior_salto'],
            'isolatedCount': row['isoladas'],
            'qdls': _safe_json_loads(row['qdls'], []),
            'digitStats': _safe_json_loads(row['digit_stats'], {'units': {}, 'tens': {}}),
        })
    return results


def _build_dia_da_sorte_bets_filters(data: dict) -> tuple[str, tuple[int, ...], int, int]:
    conditions: list[str] = []
    params: list[int] = []

    def _add_range(min_val, max_val, column):
        if min_val is not None:
            conditions.append(f"{column} >= ?")
            params.append(int(min_val))
        if max_val is not None:
            conditions.append(f"{column} <= ?")
            params.append(int(max_val))

    range_mappings = [
        ('paresMin', 'paresMax', 'pares'),
        ('imparesMin', 'imparesMax', 'impares'),
        ('maxConsecMin', 'maxConsecMax', 'max_consec'),
        ('maiorSaltoMin', 'maiorSaltoMax', 'maior_salto'),
        ('isolatedMin', 'isolatedMax', 'isoladas'),
        ('nahNMin', 'nahNMax', 'nah_n'),
        ('nahAMin', 'nahAMax', 'nah_a'),
        ('nahHMin', 'nahHMax', 'nah_h'),
    ]
    for min_key, max_key, column in range_mappings:
        _add_range(data.get(min_key), data.get(max_key), column)

    qdls_min = data.get('qdlsMin') or []
    qdls_max = data.get('qdlsMax') or []
    for idx in range(5):
        column = f'qdls_s{idx + 1}'
        min_val = qdls_min[idx] if idx < len(qdls_min) else None
        max_val = qdls_max[idx] if idx < len(qdls_max) else None
        _add_range(min_val, max_val, column)

    units_min = data.get('unitsMin') or []
    units_max = data.get('unitsMax') or []
    for idx in range(10):
        column = f'unit_{idx}'
        min_val = units_min[idx] if idx < len(units_min) else None
        max_val = units_max[idx] if idx < len(units_max) else None
        _add_range(min_val, max_val, column)

    unit_pairs_expr = ' + '.join([f'CAST(unit_{idx} / 2 AS INT)' for idx in range(10)])
    unit_pairs_expr = f'({unit_pairs_expr})'
    _add_range(data.get('unitPairsMin'), data.get('unitPairsMax'), unit_pairs_expr)

    tens_min = data.get('tensMin') or []
    tens_max = data.get('tensMax') or []
    for idx in range(4):
        column = f'ten_{idx}'
        min_val = tens_min[idx] if idx < len(tens_min) else None
        max_val = tens_max[idx] if idx < len(tens_max) else None
        _add_range(min_val, max_val, column)

    where_clause = ''
    if conditions:
        where_clause = 'WHERE ' + ' AND '.join(conditions)

    limit = int(data.get('limit') or 100)
    limit = max(1, min(limit, 1000))
    offset = int(data.get('offset') or 0)
    offset = max(0, offset)

    return where_clause, tuple(params), limit, offset


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

@app.route('/api/dia-da-sorte')
def list_dia_da_sorte():
    conn = get_connection()
    if not conn:
        return jsonify({'message': 'Database indisponivel'}), 500
    try:
        cur = conn.cursor()
        limit = request.args.get('limit', type=int)
        all_results = _fetch_dia_da_sorte_results(cur)
        total = len(all_results)
        results = all_results
        if limit and limit > 0:
            results = all_results[:limit]
        summary = _compute_dia_da_sorte_summary(all_results)
        return jsonify({'total': total, 'results': results, 'summary': summary})
    finally:
        conn.close()


@app.route('/api/dia-da-sorte/resumo')
def get_dia_da_sorte_summary():
    conn = get_connection()
    if not conn:
        return jsonify({'message': 'Database indisponivel'}), 500
    try:
        cur = conn.cursor()
        results = _fetch_dia_da_sorte_results(cur)
        summary = _compute_dia_da_sorte_summary(results)
        if summary is None:
            return jsonify({'message': 'Nenhum resultado encontrado.'}), 404
        return jsonify(summary)
    finally:
        conn.close()


@app.route('/api/dia-da-sorte/ultimo')
def get_last_dia_da_sorte_result():
    conn = get_connection()
    if not conn:
        return jsonify({'message': 'Database indisponivel'}), 500
    try:
        cur = conn.cursor()
        row = cur.execute(
            '''
                SELECT concurso, data_sorteio
                FROM dia_da_sorte_results
                ORDER BY concurso DESC
                LIMIT 1
            '''
        ).fetchone()
        if not row:
            return jsonify({'message': 'Nenhum resultado encontrado.'}), 404
        return jsonify({'concurso': row['concurso'], 'dataSorteio': row['data_sorteio']})
    finally:
        conn.close()


@app.route('/api/dia-da-sorte/apostas/filtrar', methods=['POST'])
def filter_dia_da_sorte_bets():
    conn = get_connection()
    if not conn:
        return jsonify({'message': 'Database indisponivel'}), 500
    data = request.get_json(silent=True) or {}
    try:
        cur = conn.cursor()
        where_clause, params_tuple, limit, offset = _build_dia_da_sorte_bets_filters(data)

        total = cur.execute(
            f'SELECT COUNT(*) FROM dia_da_sorte_bets {where_clause}',
            params_tuple,
        ).fetchone()[0]

        rows = cur.execute(
            f'''
                SELECT
                    d1, d2, d3, d4, d5, d6, d7,
                    pares, impares, max_consec, maior_salto, isoladas,
                    nah_n, nah_a, nah_h,
                    qdls_s1, qdls_s2, qdls_s3, qdls_s4, qdls_s5,
                    unit_0, unit_1, unit_2, unit_3, unit_4, unit_5, unit_6, unit_7, unit_8, unit_9,
                    ten_0, ten_1, ten_2, ten_3
                FROM dia_da_sorte_bets
                {where_clause}
                ORDER BY id
                LIMIT ? OFFSET ?
            ''',
            params_tuple + (limit, offset),
        ).fetchall()

        def _build_digit_map(prefix: str, count: int, row):
            return {str(i): row[f'{prefix}{i}'] for i in range(count)}

        results = [
            {
                'dezenas': [row['d1'], row['d2'], row['d3'], row['d4'], row['d5'], row['d6'], row['d7']],
                'pares': row['pares'],
                'impares': row['impares'],
                'maxConsec': row['max_consec'],
                'maiorSalto': row['maior_salto'],
                'isolatedCount': row['isoladas'],
                'nahN': row['nah_n'],
                'nahA': row['nah_a'],
                'nahH': row['nah_h'],
                'qdls': [row['qdls_s1'], row['qdls_s2'], row['qdls_s3'], row['qdls_s4'], row['qdls_s5']],
                'digitStats': {
                    'units': _build_digit_map('unit_', 10, row),
                    'tens': _build_digit_map('ten_', 4, row),
                },
            }
            for row in rows
        ]
        return jsonify({'total': total, 'limit': limit, 'offset': offset, 'results': results})
    finally:
        conn.close()


@app.route('/api/dia-da-sorte/apostas/salvar', methods=['POST'])
def save_dia_da_sorte_bets():
    conn = get_write_connection()
    if not conn:
        return jsonify({'message': 'Database indisponivel'}), 500
    data = request.get_json(silent=True) or {}
    try:
        cur = conn.cursor()
        where_clause, params_tuple, _, _ = _build_dia_da_sorte_bets_filters(data)

        total_matches = cur.execute(
            f'SELECT COUNT(*) FROM dia_da_sorte_bets {where_clause}',
            params_tuple,
        ).fetchone()[0]

        if total_matches == 0:
            return jsonify({
                'nextConcurso': None,
                'totalMatches': 0,
                'inserted': 0,
                'alreadySaved': 0,
                'message': 'Nenhuma aposta encontrada para salvar.'
            })

        last_concurso = cur.execute(
            'SELECT MAX(concurso) FROM dia_da_sorte_results'
        ).fetchone()[0]
        if last_concurso is None:
            return jsonify({'message': 'Nenhum resultado cadastrado para calcular o proximo concurso.'}), 400
        next_concurso = last_concurso + 1

        _ensure_saved_bets_table(cur)

        select_cur = conn.cursor()
        select_sql = f'''
            SELECT d1, d2, d3, d4, d5, d6, d7
            FROM dia_da_sorte_bets
            {where_clause}
            ORDER BY id
        '''

        insert_sql = '''
            INSERT OR IGNORE INTO dia_da_sorte_saved_bets (
                concurso, d1, d2, d3, d4, d5, d6, d7, acertos
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        '''

        initial_changes = conn.total_changes
        batch = []
        for row in select_cur.execute(select_sql, params_tuple):
            batch.append((next_concurso, row['d1'], row['d2'], row['d3'], row['d4'], row['d5'], row['d6'], row['d7']))
            if len(batch) >= 1000:
                cur.executemany(insert_sql, batch)
                batch.clear()
        if batch:
            cur.executemany(insert_sql, batch)

        inserted = conn.total_changes - initial_changes
        already_saved = max(total_matches - inserted, 0)
        conn.commit()
        return jsonify({
            'nextConcurso': next_concurso,
            'totalMatches': total_matches,
            'inserted': inserted,
            'alreadySaved': already_saved
        })
    finally:
        conn.close()


@app.route('/api/dia-da-sorte/apostas/salvas', methods=['GET'])
def list_saved_dia_da_sorte_bets():
    conn = get_write_connection()
    if not conn:
        return jsonify({'message': 'Database indisponivel'}), 500
    concurso_param = request.args.get('concurso', type=int)
    try:
        cur = conn.cursor()
        _ensure_saved_bets_table(cur)

        params: list[int] = []
        where_clause = ''
        if concurso_param is not None:
            where_clause = 'WHERE sb.concurso = ?'
            params.append(concurso_param)

        rows = cur.execute(
            f'''
                SELECT
                    sb.id,
                    sb.concurso,
                    sb.d1, sb.d2, sb.d3, sb.d4, sb.d5, sb.d6, sb.d7,
                    sb.acertos,
                    sb.created_at,
                    r.data_sorteio,
                    r.bola1, r.bola2, r.bola3, r.bola4, r.bola5, r.bola6, r.bola7
                FROM dia_da_sorte_saved_bets sb
                LEFT JOIN dia_da_sorte_results r ON r.concurso = sb.concurso
                {where_clause}
                ORDER BY sb.concurso DESC, sb.id ASC
            ''',
            tuple(params),
        ).fetchall()

        updates: list[tuple[int, int]] = []
        results = []
        for row in rows:
            dezenas = [row['d1'], row['d2'], row['d3'], row['d4'], row['d5'], row['d6'], row['d7']]
            resultado = None
            calculado = None

            if row['bola1'] is not None:
                resultado = [
                    row['bola1'],
                    row['bola2'],
                    row['bola3'],
                    row['bola4'],
                    row['bola5'],
                    row['bola6'],
                    row['bola7'],
                ]
                calculado = len(set(dezenas) & set(resultado))
                if calculado != row['acertos']:
                    updates.append((calculado, row['id']))

            results.append({
                'id': row['id'],
                'concurso': row['concurso'],
                'dezenas': dezenas,
                'acertos': calculado if calculado is not None else None,
                'acertosRegistrados': row['acertos'],
                'resultadoDisponivel': calculado is not None,
                'resultado': resultado,
                'dataSorteio': row['data_sorteio'],
                'createdAt': row['created_at'],
            })

        if updates:
            cur.executemany(
                'UPDATE dia_da_sorte_saved_bets SET acertos = ? WHERE id = ?',
                updates,
            )
            conn.commit()

        return jsonify({'total': len(results), 'results': results})
    finally:
        conn.close()


@app.route('/api/dia-da-sorte/apostas/salvas', methods=['DELETE'])
def delete_saved_dia_da_sorte_bets():
    conn = get_write_connection()
    if not conn:
        return jsonify({'message': 'Database indisponivel'}), 500
    concurso_param = request.args.get('concurso', type=int)
    data = request.get_json(silent=True) or {}
    if concurso_param is None:
        concurso_data = data.get('concurso')
        if concurso_data is not None:
            try:
                concurso_param = int(concurso_data)
            except (TypeError, ValueError):
                concurso_param = None
    try:
        cur = conn.cursor()
        _ensure_saved_bets_table(cur)
        if concurso_param is not None:
            cur.execute(
                'DELETE FROM dia_da_sorte_saved_bets WHERE concurso = ?',
                (concurso_param,),
            )
        else:
            cur.execute('DELETE FROM dia_da_sorte_saved_bets')
        deleted = cur.rowcount
        conn.commit()
        return jsonify({'deleted': deleted, 'concurso': concurso_param})
    finally:
        conn.close()


@app.route('/api/dia-da-sorte/apostas/enviar', methods=['POST'])
def enviar_dia_da_sorte_bets():
    data = request.get_json(silent=True) or {}
    concurso_param = data.get('concurso')
    limit_param = data.get('limit')
    shuffle_param = data.get('shuffle')
    concurso: Optional[int]
    if concurso_param is not None:
        try:
            concurso = int(concurso_param)
        except (TypeError, ValueError):
            return jsonify({'message': 'Parametro concurso invalido.'}), 400
    else:
        concurso = None

    limit: Optional[int]
    if limit_param is not None:
        try:
            limit = int(limit_param)
            if limit <= 0:
                limit = None
        except (TypeError, ValueError):
            return jsonify({'message': 'Parametro limit invalido.'}), 400
    else:
        limit = None

    shuffle_flag = False
    if isinstance(shuffle_param, bool):
        shuffle_flag = shuffle_param
    elif isinstance(shuffle_param, str):
        shuffle_flag = shuffle_param.lower() in ('1', 'true', 'yes', 'y', 'sim')

    if not CHECKOUT_SCRIPT.exists():
        app.logger.warning('Script de checkout nao encontrado em %s', CHECKOUT_SCRIPT)
        return jsonify({
            'message': 'Script de checkout nao encontrado. Crie scripts/dia_da_sorte_checkout.py com a automacao.'
        }), 501

    args = [sys.executable, str(CHECKOUT_SCRIPT)]
    if concurso is not None:
        args += ['--concurso', str(concurso)]
    if limit is not None:
        args += ['--limit', str(limit)]
        # default to shuffle when limiting sample unless explicitly false
        if shuffle_flag:
            args += ['--shuffle']
    elif shuffle_flag:
        args += ['--shuffle']

    try:
        subprocess.Popen(args)
    except Exception as exc:
        app.logger.exception('Falha ao iniciar script de checkout: %s', exc)
        return jsonify({'message': 'Falha ao iniciar script de checkout.'}), 500

    return jsonify({
        'message': 'Script iniciado. Verifique a janela do navegador e finalize manualmente.',
        'script': str(CHECKOUT_SCRIPT),
        'concurso': concurso,
        'limit': limit,
        'shuffle': shuffle_flag,
    })


def _normalize_lotofacil_bet(value) -> Optional[list[int]]:
    try:
        dezenas = [int(x) for x in value]
    except Exception:
        return None
    dezenas = [d for d in dezenas if 1 <= d <= 25]
    dezenas = sorted(set(dezenas))
    if len(dezenas) != 15:
        return None
    return dezenas


@app.route('/api/lotofacil/apostas/salvar', methods=['POST'])
def save_lotofacil_bets():
    conn = get_write_connection()
    if not conn:
        return jsonify({'message': 'Database indisponivel'}), 500
    data = request.get_json(silent=True) or {}
    bets = data.get('bets') or []
    cutoff = data.get('cutoff')
    concurso = data.get('concurso')
    try:
        if concurso is None:
            concurso = int(cutoff) + 1
        else:
            concurso = int(concurso)
    except (TypeError, ValueError):
        return jsonify({'message': 'cutoff invalido'}), 400

    if not isinstance(bets, list) or not bets:
        return jsonify({
            'nextConcurso': concurso,
            'totalReceived': 0,
            'totalValid': 0,
            'inserted': 0,
            'alreadySaved': 0,
            'invalid': 0,
            'message': 'Nenhuma aposta informada.'
        })

    try:
        cur = conn.cursor()
        _ensure_lotofacil_saved_bets_table(cur)

        insert_sql = '''
            INSERT OR IGNORE INTO lotofacil_saved_bets (
                concurso, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, acertos
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        '''
        batch = []
        invalid = 0
        valid = 0
        initial_changes = conn.total_changes
        for bet in bets:
            dezenas = _normalize_lotofacil_bet(bet)
            if not dezenas:
                invalid += 1
                continue
            valid += 1
            batch.append((concurso, *dezenas))
            if len(batch) >= 1000:
                cur.executemany(insert_sql, batch)
                batch.clear()
        if batch:
            cur.executemany(insert_sql, batch)

        inserted = conn.total_changes - initial_changes
        already_saved = max(valid - inserted, 0)
        conn.commit()
        return jsonify({
            'nextConcurso': concurso,
            'totalReceived': len(bets),
            'totalValid': valid,
            'inserted': inserted,
            'alreadySaved': already_saved,
            'invalid': invalid,
        })
    finally:
        conn.close()


@app.route('/api/lotofacil/apostas/salvas', methods=['GET'])
def list_saved_lotofacil_bets():
    conn = get_write_connection()
    if not conn:
        return jsonify({'message': 'Database indisponivel'}), 500
    concurso_param = request.args.get('concurso', type=int)
    try:
        cur = conn.cursor()
        _ensure_lotofacil_saved_bets_table(cur)

        params: list[int] = []
        where_clause = ''
        if concurso_param is not None:
            where_clause = 'WHERE sb.concurso = ?'
            params.append(concurso_param)

        rows = cur.execute(
            f'''
                SELECT
                    sb.id,
                    sb.concurso,
                    sb.n1 AS sb_n1, sb.n2 AS sb_n2, sb.n3 AS sb_n3, sb.n4 AS sb_n4, sb.n5 AS sb_n5,
                    sb.n6 AS sb_n6, sb.n7 AS sb_n7, sb.n8 AS sb_n8, sb.n9 AS sb_n9, sb.n10 AS sb_n10,
                    sb.n11 AS sb_n11, sb.n12 AS sb_n12, sb.n13 AS sb_n13, sb.n14 AS sb_n14, sb.n15 AS sb_n15,
                    sb.acertos,
                    sb.created_at,
                    sb.registrado_em,
                    r.data AS data_sorteio,
                    r.n1 AS r_n1, r.n2 AS r_n2, r.n3 AS r_n3, r.n4 AS r_n4, r.n5 AS r_n5,
                    r.n6 AS r_n6, r.n7 AS r_n7, r.n8 AS r_n8, r.n9 AS r_n9, r.n10 AS r_n10,
                    r.n11 AS r_n11, r.n12 AS r_n12, r.n13 AS r_n13, r.n14 AS r_n14, r.n15 AS r_n15
                FROM lotofacil_saved_bets sb
                LEFT JOIN results r ON r.concurso = sb.concurso
                {where_clause}
                ORDER BY sb.concurso DESC, sb.id ASC
            ''',
            tuple(params),
        ).fetchall()

        updates: list[tuple[int, int]] = []
        results = []
        for row in rows:
            dezenas = [row[f'sb_n{i}'] for i in range(1, 16)]
            resultado = None
            calculado = None

            if row['data_sorteio'] is not None and row['r_n1'] is not None:
                resultado = [row[f'r_n{i}'] for i in range(1, 16)]
                calculado = len(set(dezenas) & set(resultado))
                if calculado != row['acertos']:
                    updates.append((calculado, row['id']))

            results.append({
                'id': row['id'],
                'concurso': row['concurso'],
                'dezenas': dezenas,
                'acertos': calculado if calculado is not None else None,
                'acertosRegistrados': row['acertos'],
                'resultadoDisponivel': calculado is not None,
                'resultado': resultado,
                'dataSorteio': row['data_sorteio'],
                'createdAt': row['created_at'],
                'registradoEm': row['registrado_em'],
            })

        if updates:
            cur.executemany(
                'UPDATE lotofacil_saved_bets SET acertos = ? WHERE id = ?',
                updates,
            )
            conn.commit()

        return jsonify({'total': len(results), 'results': results})
    finally:
        conn.close()


@app.route('/api/lotofacil/apostas/salvas', methods=['DELETE'])
def delete_saved_lotofacil_bets():
    conn = get_write_connection()
    if not conn:
        return jsonify({'message': 'Database indisponivel'}), 500
    concurso_param = request.args.get('concurso', type=int)
    data = request.get_json(silent=True) or {}
    if concurso_param is None:
        concurso_data = data.get('concurso')
        if concurso_data is not None:
            try:
                concurso_param = int(concurso_data)
            except (TypeError, ValueError):
                concurso_param = None
    try:
        cur = conn.cursor()
        _ensure_lotofacil_saved_bets_table(cur)
        if concurso_param is not None:
            cur.execute(
                'DELETE FROM lotofacil_saved_bets WHERE concurso = ?',
                (concurso_param,),
            )
        else:
            cur.execute('DELETE FROM lotofacil_saved_bets')
        deleted = cur.rowcount
        conn.commit()
        return jsonify({'deleted': deleted, 'concurso': concurso_param})
    finally:
        conn.close()


@app.route('/api/lotofacil/apostas/enviar', methods=['POST'])
def enviar_lotofacil_bets():
    data = request.get_json(silent=True) or {}
    concurso_param = data.get('concurso')
    limit_param = data.get('limit')
    shuffle_param = data.get('shuffle')
    between_delay_param = data.get('betweenDelay')
    login_wait_param = data.get('loginWait')
    retry_delay_param = data.get('retryDelay')
    implicit_wait_param = data.get('implicitWait')
    concurso: Optional[int]
    if concurso_param is not None:
        try:
            concurso = int(concurso_param)
        except (TypeError, ValueError):
            return jsonify({'message': 'Parametro concurso invalido.'}), 400
    else:
        concurso = None

    limit: Optional[int]
    if limit_param is not None:
        try:
            limit = int(limit_param)
            if limit <= 0:
                limit = None
        except (TypeError, ValueError):
            return jsonify({'message': 'Parametro limit invalido.'}), 400
    else:
        limit = None

    shuffle_flag = False
    if isinstance(shuffle_param, bool):
        shuffle_flag = shuffle_param
    elif isinstance(shuffle_param, str):
        shuffle_flag = shuffle_param.lower() in ('1', 'true', 'yes', 'y', 'sim')

    def _parse_non_negative_float(value, field_name: str) -> Optional[float]:
        if value is None:
            return None
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            raise ValueError(field_name)
        if parsed < 0:
            raise ValueError(field_name)
        return parsed

    try:
        between_delay = _parse_non_negative_float(between_delay_param, 'betweenDelay')
        login_wait = _parse_non_negative_float(login_wait_param, 'loginWait')
        retry_delay = _parse_non_negative_float(retry_delay_param, 'retryDelay')
        implicit_wait = _parse_non_negative_float(implicit_wait_param, 'implicitWait')
    except ValueError as exc:
        return jsonify({'message': f'Parametro {exc.args[0]} invalido.'}), 400

    if not LOTOFACIL_CHECKOUT_SCRIPT.exists():
        app.logger.warning('Script de checkout nao encontrado em %s', LOTOFACIL_CHECKOUT_SCRIPT)
        return jsonify({
            'message': 'Script de checkout nao encontrado. Crie scripts/lotofacil_checkout.py com a automacao.'
        }), 501

    args = [sys.executable, str(LOTOFACIL_CHECKOUT_SCRIPT)]
    if concurso is not None:
        args += ['--concurso', str(concurso)]
    if limit is not None:
        args += ['--limit', str(limit)]
        if shuffle_flag:
            args += ['--shuffle']
    elif shuffle_flag:
        args += ['--shuffle']
    if between_delay is not None:
        args += ['--between-delay', str(between_delay)]
    if login_wait is not None:
        args += ['--login-wait', str(login_wait)]
    if retry_delay is not None:
        args += ['--retry-delay', str(retry_delay)]
    if implicit_wait is not None:
        args += ['--implicit-wait', str(implicit_wait)]

    try:
        subprocess.Popen(args)
    except Exception as exc:
        app.logger.exception('Falha ao iniciar script de checkout lotofacil: %s', exc)
        return jsonify({'message': 'Falha ao iniciar script de checkout.'}), 500

    return jsonify({
        'message': 'Script iniciado. Verifique a janela do navegador e finalize manualmente.',
        'script': str(LOTOFACIL_CHECKOUT_SCRIPT),
        'concurso': concurso,
        'limit': limit,
        'shuffle': shuffle_flag,
        'betweenDelay': between_delay,
        'loginWait': login_wait,
        'retryDelay': retry_delay,
        'implicitWait': implicit_wait,
    })


@app.route('/api/lotofacil/bola-da-vez', methods=['GET'])
def get_lotofacil_bola_da_vez():
    cutoff = request.args.get('cutoff', type=int)

    conn = get_connection()
    if conn is None:
        return jsonify({'error': 'lotofacil.db not found'}), 500

    try:
        if cutoff is None:
            row = conn.execute('SELECT MAX(concurso) AS max_concurso FROM results').fetchone()
            cutoff = row['max_concurso'] if row else None

        if cutoff is None:
            return jsonify({'message': 'Nenhum concurso encontrado para calcular bola da vez.'}), 404

        rows = conn.execute(
            '''
            SELECT concurso, data, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15
            FROM results
            WHERE concurso <= ?
            ORDER BY concurso ASC
            ''',
            (cutoff,),
        ).fetchall()

        if not rows:
            return jsonify({'message': 'Nao ha historico para o cutoff informado.'}), 404

        from pipeline_filters import compute_bola_da_vez_frequencia, compute_bola_da_vez_listas

        entram, saem = compute_bola_da_vez_listas(rows)
        frequencia = compute_bola_da_vez_frequencia(rows)
        resultado_row = rows[-1]
        cutoff_usado = int(resultado_row['concurso'])
        resultado_cutoff = [int(resultado_row[f'n{i}']) for i in range(1, 16)]
        return jsonify({
            'cutoff': cutoff_usado,
            'cutoffSolicitado': cutoff,
            'totalHistorico': len(rows),
            'dataCutoff': resultado_row['data'],
            'resultadoCutoff': resultado_cutoff,
            'entram': entram,
            'saem': saem,
            'frequencia': frequencia,
        })
    finally:
        conn.close()


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
    # Default Par/Ãmpar as in notebook if none provided
    if not pares and not impares:
        pares = {6, 7, 8}
        impares = {7, 8, 9}
    concurso_limite = request.args.get('concursoLimite', type=int)
    padrao_linha = request.args.get('padraoLinha')
    soma_min = request.args.get('somaMin', type=int)
    soma_max = request.args.get('somaMax', type=int)
    if soma_min is not None and soma_max is not None and soma_min > soma_max:
        soma_min, soma_max = soma_max, soma_min
    # NAH filter: accept either a combined "nah" param (e.g., 5,3,7)
    # or separate params nahN, nahA, nahH
    nah_param = request.args.get('nah', '').strip()
    nahN_param = request.args.get('nahN', type=int)
    nahA_param = request.args.get('nahA', type=int)
    nahH_param = request.args.get('nahH', type=int)
    nah_filter = None
    if nah_param:
        try:
            parts = [p.strip() for p in nah_param.replace(';', ',').split(',') if p.strip()]
            if len(parts) == 3:
                nah_filter = (int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            nah_filter = None
    elif None not in (nahN_param, nahA_param, nahH_param):
        nah_filter = (nahN_param, nahA_param, nahH_param)

    from filters import FiltroDezenasParesImpares, FiltroConcursoLimite
    filtro_paridade = FiltroDezenasParesImpares(pares, impares, ativo=bool(pares or impares))
    filtro_limite = FiltroConcursoLimite(concurso_limite, ativo=concurso_limite is not None)

    conn = get_connection()
    if conn is None:
        app.logger.warning('lotofacil.db not found; returning empty results')
        return jsonify({'error': 'lotofacil.db not found', 'total': 0, 'results': []}), 500
    cur = conn.execute(
        'SELECT concurso, data, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, ganhador '
        'FROM results ORDER BY concurso ASC'
    )
    rows_all = cur.fetchall()
    conn.close()

    # Precompute NAH counts (N, A, H) for each concurso based on previous draws
    def _dezenas_from_row(r):
        return [r[f'n{i}'] for i in range(1, 16)]

    nah_by_concurso = {}
    for idx, r in enumerate(rows_all):
        if idx < 2:
            nah_by_concurso[r['concurso']] = (None, None, None)
            continue
        current = set(_dezenas_from_row(rows_all[idx]))
        prev = set(_dezenas_from_row(rows_all[idx - 1]))
        prev2 = set(_dezenas_from_row(rows_all[idx - 2]))
        N = current - prev
        A = (current & prev) - prev2
        H = current & prev & prev2
        nah_by_concurso[r['concurso']] = (len(N), len(A), len(H))

    # Apply existing filters
    rows = filtro_paridade.apply(rows_all)
    rows = filtro_limite.apply(rows)

    results = []
    for r in rows:
        dezenas = [r[f'n{i}'] for i in range(1, 16)]
        soma_dezenas = sum(dezenas)
        qtd_pares = sum(1 for d in dezenas if d % 2 == 0)
        qtd_impares = len(dezenas) - qtd_pares
        lines = [0]*5
        for d in dezenas:
            lines[(d-1)//5] += 1
        padrao = classify_pattern(lines)
        n_val, a_val, h_val = nah_by_concurso.get(r['concurso'], (None, None, None))
        if nah_filter and (n_val, a_val, h_val) != nah_filter:
            continue
        if padrao_linha and padrao != padrao_linha:
            continue
        if soma_min is not None and soma_dezenas < soma_min:
            continue
        if soma_max is not None and soma_dezenas > soma_max:
            continue

        results.append({
            'concurso': r['concurso'],
            'data': r['data'],
            'dezenas': dezenas,
            'somaDezenas': soma_dezenas,
            'ganhador': r['ganhador'],
            'qtdPares': qtd_pares,
            'qtdImpares': qtd_impares,
            'padraoLinha': padrao,
            'nahN': n_val,
            'nahA': a_val,
            'nahH': h_val,
        })
    results.sort(key=lambda x: x['concurso'], reverse=True)
    total = len(results)

    nah_transition_summary = []
    nah_transition_pairs = []
    nah_transition_total = 0
    nah_transition_current = None
    if nah_filter:
        nah_transition_current = list(nah_filter)
        transition_counter = Counter()
        max_pairs = request.args.get('nahTransitionLimit', default=50, type=int)
        max_pairs = max(0, min(max_pairs, 500))
        for item in results:
            cur_tuple = (item.get('nahN'), item.get('nahA'), item.get('nahH'))
            if None in cur_tuple or cur_tuple != nah_filter:
                continue
            if concurso_limite is not None and item['concurso'] + 1 > concurso_limite:
                continue
            next_tuple = nah_by_concurso.get(item['concurso'] + 1)
            if not next_tuple or None in next_tuple:
                continue
            transition_counter[next_tuple] += 1
            nah_transition_total += 1
            if max_pairs and len(nah_transition_pairs) < max_pairs:
                nah_transition_pairs.append({
                    'ccCurrent': item['concurso'],
                    'ccNext': item['concurso'] + 1,
                    'currentNah': list(cur_tuple),
                    'nextNah': list(next_tuple),
                })
        nah_transition_summary = [
            {'nah': list(key), 'count': count}
            for key, count in transition_counter.most_common()
        ]

    return jsonify({
        'total': total,
        'results': results[:500],
        'nahTransitionCurrent': nah_transition_current,
        'nahTransitionSummary': nah_transition_summary,
        'nahTransitionTotal': nah_transition_total,
        'nahTransitionPairs': nah_transition_pairs,
    })


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
    total = len(results)
    return jsonify({'total': total, 'results': results[:10]})

@app.route('/api/selecionar-filtros')
def selecionar_por_filtros():
    """Replica aproximada do pipeline de 12 filtros do notebook.

    ParÃ¢metros (query):
      - cutoff: concurso base (usa histÃ³rico atÃ© ele e calcula NAH para ele)
      - aplicarCRE (bool, default true): aplica countCRE < 2
      - aplicarSalto (bool, default true): aplica maiorSalto in [3,4]
      - colMin, colMax: vetores de 5 inteiros (ex: "2,1,1,1,1" e "5,5,4,5,5")
      - aplicarNAH (bool, default true): usa variaÃ§Ãµes em torno do NAH base
      - nahVar (int, default 2): variaÃ§Ã£o +- para N/A/H
      - aplicarABCD (bool, default true): usa combFreq com min/max defaults
      - abcdMin, abcdMax: vetores de 4 inteiros
      - aplicarNo3Consec (bool, default true): remove apostas com sequÃªncias de 3+
      - pares, impares: filtros opcionais (contagem permitida)
      - limit: mÃ¡ximo de apostas retornadas (default 200)
    """
    from filters import FiltroDezenasParesImpares
    from selector import compute_number_frequencies, score_bet, select_diverse
    from pipeline_filters import (
        dezenas_from_row, count_par_impar, max_jump, count_columns, count_cre,
        filter_by_vector, compute_freq_groups, count_groups,
        generate_nah_variations, compute_mapping_sets, has_line_three_consecutives_3L,
        bola_da_vez, in_losango_ou_centro, maximo_um_cinco,
        minimo_um_quatro, tem_dezena_onze_ou_quinze, countcs_em_valores,
        filtro_cantos, filtro_diagonais, compute_bola_da_vez_listas
    )

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

    def _parse_vec(param: str, length: int) -> list | None:
        if not param:
            return None
        try:
            parts = [int(p.strip()) for p in param.split(',')]
            if len(parts) != length:
                return None
            return parts
        except Exception:
            return None

    def _parse_csv_ints(param: str) -> list[int]:
        if not param:
            return []
        out: list[int] = []
        for part in param.replace(';', ',').split(','):
            part = part.strip()
            if not part:
                continue
            try:
                out.append(int(part))
            except ValueError:
                continue
        return out

    def _bool(name: str, default: bool) -> bool:
        v = request.args.get(name)
        if v is None:
            return default
        return v.lower() in ('1', 'true', 'sim', 'yes', 'y')

    def _parse_nah_list(param: str) -> list[tuple[int, int, int]]:
        if not param:
            return []
        items: list[tuple[int, int, int]] = []
        for raw in param.replace('|', ';').replace('\n', ';').split(';'):
            chunk = raw.strip().strip('()')
            if not chunk:
                continue
            parts = re.findall(r'-?\d+', chunk)
            if len(parts) != 3:
                continue
            try:
                t = (int(parts[0]), int(parts[1]), int(parts[2]))
            except ValueError:
                continue
            if any(n < 0 for n in t) or sum(t) != 15:
                continue
            items.append(t)
        return items

    cutoff = request.args.get('cutoff', type=int)
    aplicar_cre = _bool('aplicarCRE', True)
    aplicar_salto = _bool('aplicarSalto', True)
    aplicar_col = True
    aplicar_nah = _bool('aplicarNAH', True)
    nah_var = request.args.get('nahVar', default=2, type=int)
    nah_list_param = request.args.get('nahList', '')
    nah_list = _parse_nah_list(nah_list_param)
    nah_list_provided = bool(nah_list_param.strip())
    if nah_list_provided:
        aplicar_nah = True
    aplicar_abcd = _bool('aplicarABCD', True)
    aplicar_tres = _bool('aplicarTresConsec', True)
    # Missing notebook filters (optional, toggled by checkbox in UI)
    aplicar_bola_vez = _bool('aplicarBolaVez', False)
    aplicar_losango = _bool('aplicarLosangoCentro', False)
    aplicar_onze_quinze = _bool('aplicarOnzeQuinze', False)
    aplicar_countc_min_um_quatro = _bool('aplicarCountCMinUmQuatro', False)
    aplicar_max_um_cinco = _bool('aplicarMaxUmCinco', False)
    aplicar_countcs = _bool('aplicarCountCS', False)
    aplicar_cantos = _bool('aplicarCantos', False)
    aplicar_diagonais = _bool('aplicarDiagonais', False)
    aplicar_soma = _bool('aplicarSoma', False)
    soma_min = request.args.get('somaMin', default=None, type=int)
    soma_max = request.args.get('somaMax', default=None, type=int)
    if soma_min is not None and soma_max is not None and soma_min > soma_max:
        soma_min, soma_max = soma_max, soma_min
    aplicar_pi = _bool('aplicarPI', True)
    limit = request.args.get('limit', default=200, type=int)
    selection_mode = (request.args.get('selectionMode') or 'random').strip().lower()
    selection_seed = request.args.get('selectionSeed', default=None, type=int)

    col_min = _parse_vec(request.args.get('colMin', ''), 5) or [2, 1, 1, 1, 1]
    col_max = _parse_vec(request.args.get('colMax', ''), 5) or [5, 5, 4, 5, 5]
    abcd_min = _parse_vec(request.args.get('abcdMin', ''), 4) or [0, 2, 4, 0]
    abcd_max = _parse_vec(request.args.get('abcdMax', ''), 4) or [3, 8, 10, 5]
    # bola-da-vez lists (optional overrides from query)
    entram_list = _parse_csv_ints(request.args.get('bolaVezEntram', ''))
    saem_list = _parse_csv_ints(request.args.get('bolaVezSaem', ''))

    pares_param = request.args.get('pares', '')
    impares_param = request.args.get('impares', '')
    pares = _parse_int_list(request.args.getlist('pares') or [pares_param])
    impares = _parse_int_list(request.args.getlist('impares') or [impares_param])

    # Load bets (3 por linha)
    csv_path = Path(__file__).resolve().parent.parent / 'todasTresPorLinha.csv'
    with csv_path.open(newline='') as f:
        reader = csv.DictReader(f)
        bets = []
        for idx, row in enumerate(reader, start=1):
            data_row = {f'n{i}': int(row[f'B{i}']) for i in range(1, 16)}
            data_row['concurso'] = idx
            bets.append(data_row)

    # Par/Impar allowed counts filter (controlled by aplicarPI)
    if aplicar_pi:
        # Use defaults from notebook if none provided
        if not pares and not impares:
            pares = {6, 7, 8}
            impares = {7, 8, 9}
        filtro_paridade = FiltroDezenasParesImpares(pares, impares, ativo=True)
        bets = filtro_paridade.apply(bets)

    # Load historical results for freq groups and NAH
    conn = get_connection()
    if conn is None:
        return jsonify({'error': 'lotofacil.db not found'}), 500
    if cutoff is not None:
        cur = conn.execute(
            'SELECT concurso, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, data, ganhador FROM results WHERE concurso <= ? ORDER BY concurso ASC',
            (cutoff,)
        )
    else:
        cur = conn.execute(
            'SELECT concurso, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, data, ganhador FROM results ORDER BY concurso ASC'
        )
    hist = cur.fetchall()
    conn.close()
    if len(hist) < 3:
        return jsonify({'error': 'histÃ³rico insuficiente para NAH'}), 400

    if aplicar_bola_vez and not entram_list and not saem_list:
        entram_list, saem_list = compute_bola_da_vez_listas(hist)

    # Build frequency groups from historical results
    freqs = compute_number_frequencies(hist)
    groups = compute_freq_groups(freqs)

    # NAH mapping based on last three results up to cutoff
    last = dezenas_from_row(hist[-1])
    prev1 = dezenas_from_row(hist[-2])
    prev2 = dezenas_from_row(hist[-3])
    # NAH base for last result
    N_base = len(set(last) - set(prev1))
    A_base = len((set(last) & set(prev1)) - set(prev2))
    H_base = len(set(last) & set(prev1) & set(prev2))
    nah_base = (N_base, A_base, H_base)
    # mapping sets for classifying bets relative to last result
    NS_to_N, N_to_A, AH_to_H = compute_mapping_sets(last, prev1, prev2)
    if aplicar_nah:
        if nah_list_provided:
            allowed_nah = set(nah_list)
        else:
            allowed_nah = set(generate_nah_variations(nah_base, var_range=nah_var))
    else:
        allowed_nah = set()

    # Apply pipeline filters
    filtradas = []
    for r in bets:
        dz = dezenas_from_row(r)
        countN = sum(1 for d in dz if d in NS_to_N)
        countA = sum(1 for d in dz if d in N_to_A)
        countH = sum(1 for d in dz if d in AH_to_H)
        # step CRE
        if aplicar_cre:
            if count_cre(dz) >= 2:
                continue
        # step maior salto
        if aplicar_salto:
            mj = max_jump(dz)
            if mj not in (3, 4):
                continue
        # step coluna counts
        if aplicar_col:
            cols = count_columns(dz)
            if not filter_by_vector(cols, col_min, col_max):
                continue
        if aplicar_soma:
            soma = sum(dz)
            if soma_min is not None and soma < soma_min:
                continue
            if soma_max is not None and soma > soma_max:
                continue
        # step NAH
        if aplicar_nah:
            if (countN, countA, countH) not in allowed_nah:
                continue
        # step ABCD
        if aplicar_abcd:
            cnts, _ = count_groups(dz, groups)
            if not filter_by_vector(cnts, abcd_min, abcd_max):
                continue
        # step 3 consecutivos na linha (notebook rule)
        if aplicar_tres:
            if not has_line_three_consecutives_3L(dz):
                continue
        # step 7) bola da vez (at least one prediction from "entram" or "saem")
        if aplicar_bola_vez:
            if not bola_da_vez(dz, entram_list, saem_list):
                continue
        # step 8) losango ou centro
        if aplicar_losango:
            if not in_losango_ou_centro(dz):
                continue
        # step 9) 11_15 (contains 11 or 15)
        if aplicar_onze_quinze:
            if not tem_dezena_onze_ou_quinze(dz):
                continue
        # step 10) countC: at least one "4"
        if aplicar_countc_min_um_quatro:
            if not minimo_um_quatro(dz):
                continue
        # step 11) countC: at most one "5"
        if aplicar_max_um_cinco:
            if not maximo_um_cinco(dz):
                continue
        # step 12) consecutivos gerais (countCS in [2,3,4,5])
        if aplicar_countcs:
            if not countcs_em_valores(dz, (2, 3, 4, 5)):
                continue
        # step 13) cantos (at least two of 1,5,21,25)
        if aplicar_cantos:
            if not filtro_cantos(dz, minimo=2):
                continue
        # step 14) diagonais (notebook rule)
        if aplicar_diagonais:
            if not filtro_diagonais(dz):
                continue
        filtradas.append({
            'dezenas': dz,
            'id': r.get('concurso'),
            'nahN': countN,
            'nahA': countA,
            'nahH': countH,
        })

    rng = random.Random(selection_seed) if selection_seed is not None else random

    def _select_first(items: list[dict], k: int) -> list[dict]:
        if k >= len(items):
            return items
        return items[:k]

    def _select_random(items: list[dict], k: int) -> list[dict]:
        if k >= len(items):
            return items
        return rng.sample(items, k)

    def _select_diverse(items: list[dict], k: int) -> list[dict]:
        if k >= len(items):
            return items
        scored = []
        for item in items:
            sc = score_bet(item['dezenas'], freqs)
            scored.append((item['dezenas'], sc))
        pool_size = max(k * 5, 200)
        selected_pairs = select_diverse(scored, k=k, greedy_pool=pool_size)
        index = {tuple(it['dezenas']): it for it in items}
        selected = []
        for dezenas, _ in selected_pairs:
            it = index.get(tuple(dezenas))
            if it is not None:
                selected.append(it)
        # fallback if mapping misses any
        if len(selected) < k:
            remaining = [it for it in items if it not in selected]
            selected.extend(remaining[: k - len(selected)])
        return selected

    def _select_stratified(items: list[dict], k: int) -> list[dict]:
        if k >= len(items):
            return items
        buckets = defaultdict(list)
        for item in items:
            cnts, _ = count_groups(item['dezenas'], groups)
            buckets[tuple(cnts)].append(item)

        total = len(items)
        bucket_info = []
        for key, bucket in buckets.items():
            exact = (len(bucket) * k) / total
            base = int(math.floor(exact))
            bucket_info.append([key, base, exact - base])

        remaining = k - sum(info[1] for info in bucket_info)
        bucket_info.sort(key=lambda x: x[2], reverse=True)
        for idx in range(remaining):
            bucket_info[idx % len(bucket_info)][1] += 1

        selected = []
        leftovers = []
        for key, quota, _ in bucket_info:
            bucket = list(buckets[key])
            rng.shuffle(bucket)
            take = min(quota, len(bucket))
            selected.extend(bucket[:take])
            leftovers.extend(bucket[take:])

        if len(selected) < k and leftovers:
            need = k - len(selected)
            if need >= len(leftovers):
                selected.extend(leftovers)
            else:
                selected.extend(rng.sample(leftovers, need))
        return selected

    def _select_distant(items: list[dict], k: int) -> list[dict]:
        if k >= len(items):
            return items
        ordered = sorted(items, key=lambda it: (it.get('id') or 0))
        step = (len(ordered) - 1) / (k - 1) if k > 1 else 0
        indices = [int(math.floor(i * step)) for i in range(k)]
        return [ordered[i] for i in indices]

    filtered_total = len(filtradas)
    selected = filtradas
    if limit and filtered_total > limit:
        if selection_mode in ('primeiras', 'primeiro', 'first', 'firsts'):
            selected = _select_first(filtradas, limit)
        elif selection_mode in ('diversidade', 'diversity', 'jaccard'):
            selected = _select_diverse(filtradas, limit)
        elif selection_mode in ('estratificada', 'stratified', 'grupos', 'grupo'):
            selected = _select_stratified(filtradas, limit)
        elif selection_mode in ('distantes', 'distante', 'id', 'ids'):
            selected = _select_distant(filtradas, limit)
        else:
            selected = _select_random(filtradas, limit)

    return jsonify({
        'totalBase': len(bets),
        'cutoff': cutoff,
        'nahBase': nah_base,
        'nahAllowed': sorted(list(allowed_nah)) if aplicar_nah else [],
        'nahList': [list(item) for item in nah_list],
        'nahListProvided': nah_list_provided,
        'aplicarCRE': aplicar_cre,
        'aplicarSalto': aplicar_salto,
        'colMin': col_min,
        'colMax': col_max,
        'aplicarNAH': aplicar_nah,
        'nahVar': nah_var,
        'aplicarABCD': aplicar_abcd,
        'abcdMin': abcd_min,
        'abcdMax': abcd_max,
        'aplicarTresConsec': aplicar_tres,
        'aplicarBolaVez': aplicar_bola_vez,
        'bolaVezEntram': entram_list,
        'bolaVezSaem': saem_list,
        'aplicarLosangoCentro': aplicar_losango,
        'aplicarOnzeQuinze': aplicar_onze_quinze,
        'aplicarCountCMinUmQuatro': aplicar_countc_min_um_quatro,
        'aplicarMaxUmCinco': aplicar_max_um_cinco,
        'aplicarCountCS': aplicar_countcs,
        'aplicarCantos': aplicar_cantos,
        'aplicarDiagonais': aplicar_diagonais,
        'aplicarSoma': aplicar_soma,
        'somaMin': soma_min,
        'somaMax': soma_max,
        'aplicarPI': aplicar_pi,
        'selectionMode': selection_mode,
        'selectionSeed': selection_seed,
        'results': [
            {
                'id': item.get('id'),
                'dezenas': sorted(item['dezenas']),
                'qtdPares': count_par_impar(item['dezenas'])[0],
                'qtdImpares': 15 - count_par_impar(item['dezenas'])[0],
                'nahN': item.get('nahN'),
                'nahA': item.get('nahA'),
                'nahH': item.get('nahH'),
            }
            for item in selected
        ],
        'totalFiltrado': len(filtradas),
        'limit': limit,
    })

@app.route('/api/selecionar-filtros/backtest')
def backtest_selecionar_por_filtros():
    from filters import FiltroDezenasParesImpares
    from selector import compute_number_frequencies, score_bet, select_diverse
    from pipeline_filters import (
        dezenas_from_row, max_jump, count_columns, count_cre,
        filter_by_vector, compute_freq_groups, count_groups,
        generate_nah_variations, compute_mapping_sets, has_line_three_consecutives_3L,
        bola_da_vez, in_losango_ou_centro, maximo_um_cinco,
        minimo_um_quatro, tem_dezena_onze_ou_quinze, countcs_em_valores,
        filtro_cantos, filtro_diagonais, compute_bola_da_vez_listas
    )

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

    def _parse_vec(param: str, length: int) -> list | None:
        if not param:
            return None
        try:
            parts = [int(p.strip()) for p in param.split(',')]
            if len(parts) != length:
                return None
            return parts
        except Exception:
            return None

    def _parse_csv_ints(param: str) -> list[int]:
        if not param:
            return []
        out: list[int] = []
        for part in param.replace(';', ',').split(','):
            part = part.strip()
            if not part:
                continue
            try:
                out.append(int(part))
            except ValueError:
                continue
        return out

    def _bool(name: str, default: bool) -> bool:
        v = request.args.get(name)
        if v is None:
            return default
        return v.lower() in ('1', 'true', 'sim', 'yes', 'y')

    def _parse_nah_list(param: str) -> list[tuple[int, int, int]]:
        if not param:
            return []
        items: list[tuple[int, int, int]] = []
        for raw in param.replace('|', ';').replace('\n', ';').split(';'):
            chunk = raw.strip().strip('()')
            if not chunk:
                continue
            parts = re.findall(r'-?\d+', chunk)
            if len(parts) != 3:
                continue
            try:
                t = (int(parts[0]), int(parts[1]), int(parts[2]))
            except ValueError:
                continue
            if any(n < 0 for n in t) or sum(t) != 15:
                continue
            items.append(t)
        return items

    def _normalize_selection_mode(mode: str) -> str:
        raw = (mode or '').strip().lower()
        if raw in ('primeiras', 'primeiro', 'first', 'firsts'):
            return 'primeiras'
        if raw in ('diversidade', 'diversity', 'jaccard'):
            return 'diversidade'
        if raw in ('estratificada', 'stratified', 'grupos', 'grupo'):
            return 'estratificada'
        if raw in ('distantes', 'distante', 'id', 'ids'):
            return 'distantes'
        return 'random'

    def _select_first(items: list[dict], k: int) -> list[dict]:
        if k >= len(items):
            return items
        return items[:k]

    def _select_random(items: list[dict], k: int, rng: random.Random) -> list[dict]:
        if k >= len(items):
            return items
        return rng.sample(items, k)

    def _select_diverse(items: list[dict], k: int, freqs: dict, rng: random.Random) -> list[dict]:
        if k >= len(items):
            return items
        scored = []
        for item in items:
            sc = score_bet(item['dezenas'], freqs)
            scored.append((item['dezenas'], sc))
        pool_size = max(k * 5, 200)
        selected_pairs = select_diverse(scored, k=k, greedy_pool=pool_size)
        index = {tuple(it['dezenas']): it for it in items}
        selected = []
        for dezenas, _ in selected_pairs:
            it = index.get(tuple(dezenas))
            if it is not None:
                selected.append(it)
        if len(selected) < k:
            remaining = [it for it in items if it not in selected]
            rng.shuffle(remaining)
            selected.extend(remaining[: k - len(selected)])
        return selected

    def _select_stratified(items: list[dict], k: int, groups: dict, rng: random.Random) -> list[dict]:
        if k >= len(items):
            return items
        buckets = defaultdict(list)
        for item in items:
            cnts, _ = count_groups(item['dezenas'], groups)
            buckets[tuple(cnts)].append(item)

        total = len(items)
        bucket_info = []
        for key, bucket in buckets.items():
            exact = (len(bucket) * k) / total
            base = int(math.floor(exact))
            bucket_info.append([key, base, exact - base])

        remaining = k - sum(info[1] for info in bucket_info)
        bucket_info.sort(key=lambda x: x[2], reverse=True)
        for idx in range(remaining):
            bucket_info[idx % len(bucket_info)][1] += 1

        selected = []
        leftovers = []
        for key, quota, _ in bucket_info:
            bucket = list(buckets[key])
            rng.shuffle(bucket)
            take = min(quota, len(bucket))
            selected.extend(bucket[:take])
            leftovers.extend(bucket[take:])

        if len(selected) < k and leftovers:
            need = k - len(selected)
            if need >= len(leftovers):
                selected.extend(leftovers)
            else:
                selected.extend(rng.sample(leftovers, need))
        return selected

    def _select_distant(items: list[dict], k: int) -> list[dict]:
        if k >= len(items):
            return items
        ordered = sorted(items, key=lambda it: (it.get('id') or 0))
        step = (len(ordered) - 1) / (k - 1) if k > 1 else 0
        indices = [int(math.floor(i * step)) for i in range(k)]
        return [ordered[i] for i in indices]

    cutoff = request.args.get('cutoff', type=int)
    aplicar_cre = _bool('aplicarCRE', True)
    aplicar_salto = _bool('aplicarSalto', True)
    aplicar_col = True
    aplicar_nah = _bool('aplicarNAH', True)
    nah_var = request.args.get('nahVar', default=2, type=int)
    nah_list_param = request.args.get('nahList', '')
    nah_list = _parse_nah_list(nah_list_param)
    nah_list_provided = bool(nah_list_param.strip())
    if nah_list_provided:
        aplicar_nah = True
    aplicar_abcd = _bool('aplicarABCD', True)
    aplicar_tres = _bool('aplicarTresConsec', True)
    aplicar_bola_vez = _bool('aplicarBolaVez', False)
    aplicar_losango = _bool('aplicarLosangoCentro', False)
    aplicar_onze_quinze = _bool('aplicarOnzeQuinze', False)
    aplicar_countc_min_um_quatro = _bool('aplicarCountCMinUmQuatro', False)
    aplicar_max_um_cinco = _bool('aplicarMaxUmCinco', False)
    aplicar_countcs = _bool('aplicarCountCS', False)
    aplicar_cantos = _bool('aplicarCantos', False)
    aplicar_diagonais = _bool('aplicarDiagonais', False)
    aplicar_soma = _bool('aplicarSoma', False)
    soma_min = request.args.get('somaMin', default=None, type=int)
    soma_max = request.args.get('somaMax', default=None, type=int)
    if soma_min is not None and soma_max is not None and soma_min > soma_max:
        soma_min, soma_max = soma_max, soma_min
    aplicar_pi = _bool('aplicarPI', True)

    col_min = _parse_vec(request.args.get('colMin', ''), 5) or [2, 1, 1, 1, 1]
    col_max = _parse_vec(request.args.get('colMax', ''), 5) or [5, 5, 4, 5, 5]
    abcd_min = _parse_vec(request.args.get('abcdMin', ''), 4) or [0, 2, 4, 0]
    abcd_max = _parse_vec(request.args.get('abcdMax', ''), 4) or [3, 8, 10, 5]
    entram_list_base = _parse_csv_ints(request.args.get('bolaVezEntram', ''))
    saem_list_base = _parse_csv_ints(request.args.get('bolaVezSaem', ''))

    pares_param = request.args.get('pares', '')
    impares_param = request.args.get('impares', '')
    pares = _parse_int_list(request.args.getlist('pares') or [pares_param])
    impares = _parse_int_list(request.args.getlist('impares') or [impares_param])
    padrao_linha_param = (request.args.get('padraoLinha') or '').strip()
    padrao_linha_map = {
        'outro': 'outro',
        '1 linha completa': '1 linha completa',
        '3 por linha': '3 por linha',
        'quase 3 por linha': 'quase 3 por linha',
    }
    padrao_linha = None
    if padrao_linha_param and padrao_linha_param.lower() not in ('todos', 'all'):
        padrao_linha = padrao_linha_map.get(padrao_linha_param.lower())
        if not padrao_linha:
            return jsonify({
                'error': 'padraoLinha invalido',
                'validos': ['outro', '1 linha completa', '3 por linha', 'quase 3 por linha'],
            }), 400

    backtest_window = request.args.get('backtestWindow', default=60, type=int)
    backtest_window = max(1, backtest_window or 60)
    backtest_top_n = request.args.get('backtestTopN', default=100, type=int)
    backtest_top_n = max(1, backtest_top_n or 100)
    backtest_step = request.args.get('backtestStep', default=1, type=int)
    backtest_step = max(1, backtest_step or 1)
    backtest_from = request.args.get('backtestFrom', type=int)
    backtest_to = request.args.get('backtestTo', type=int)

    modes_raw = request.args.get('backtestModes', 'primeiras,diversidade,estratificada,distantes,random')
    requested_modes = []
    for part in modes_raw.replace(';', ',').split(','):
        mode = _normalize_selection_mode(part)
        if mode and mode not in requested_modes:
            requested_modes.append(mode)
    if not requested_modes:
        requested_modes = ['primeiras', 'diversidade', 'estratificada', 'distantes', 'random']

    selection_seed = request.args.get('selectionSeed', default=None, type=int)
    if selection_seed is None:
        selection_seed = 12345

    csv_path = Path(__file__).resolve().parent.parent / 'todasTresPorLinha.csv'
    with csv_path.open(newline='') as f:
        reader = csv.DictReader(f)
        bets = []
        for idx, row in enumerate(reader, start=1):
            data_row = {f'n{i}': int(row[f'B{i}']) for i in range(1, 16)}
            data_row['concurso'] = idx
            bets.append(data_row)

    if aplicar_pi:
        if not pares and not impares:
            pares = {6, 7, 8}
            impares = {7, 8, 9}
        filtro_paridade = FiltroDezenasParesImpares(pares, impares, ativo=True)
        bets = filtro_paridade.apply(bets)

    conn = get_connection()
    if conn is None:
        return jsonify({'error': 'lotofacil.db not found'}), 500
    try:
        rows = conn.execute(
            'SELECT concurso, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15, data, ganhador FROM results ORDER BY concurso ASC'
        ).fetchall()
    finally:
        conn.close()

    if len(rows) < 4:
        return jsonify({'error': 'historico insuficiente para backtest'}), 400

    concursos = [int(r['concurso']) for r in rows]
    concurso_set = set(concursos)
    idx_by_concurso = {int(r['concurso']): idx for idx, r in enumerate(rows)}

    min_cutoff = concursos[2]
    max_cutoff = concursos[-2]

    if backtest_to is None:
        backtest_to = cutoff if cutoff is not None else max_cutoff
    backtest_to = max(min_cutoff, min(max_cutoff, int(backtest_to)))

    if backtest_from is None:
        backtest_from = backtest_to - (backtest_window - 1) * backtest_step
    backtest_from = max(min_cutoff, int(backtest_from))

    cutoffs = []
    for cc in range(backtest_from, backtest_to + 1, backtest_step):
        if cc in concurso_set and (cc + 1) in concurso_set:
            cutoffs.append(cc)

    if not cutoffs:
        return jsonify({'error': 'nenhum cutoff valido para backtest'}), 400

    mode_stats = {
        mode: {
            'tests': 0,
            'hits': 0,
            'filtered_sum': 0.0,
            'selected_sum': 0.0,
            'pos_sum': 0.0,
            'pos_count': 0,
            'best_pos': None,
            'worst_pos': None,
        }
        for mode in requested_modes
    }

    details = []
    winner_in_filtered_count = 0

    for cutoff_atual in cutoffs:
        hist_idx = idx_by_concurso.get(cutoff_atual)
        if hist_idx is None:
            continue
        hist = rows[: hist_idx + 1]
        if len(hist) < 3:
            continue

        next_row = rows[hist_idx + 1] if (hist_idx + 1) < len(rows) else None
        if next_row is None:
            continue
        next_dezenas_list = [int(next_row[f'n{i}']) for i in range(1, 16)]
        next_dezenas = tuple(sorted(next_dezenas_list))
        next_lines = [0] * 5
        for d in next_dezenas_list:
            next_lines[(d - 1) // 5] += 1
        next_padrao_linha = classify_pattern(next_lines)
        if padrao_linha and next_padrao_linha != padrao_linha:
            continue

        # Backtest rule: when Bola da Vez is enabled, recalculate lists for each cutoff.
        # This avoids leaking a single cutoff's lists into the whole historical window.
        if aplicar_bola_vez:
            entram_list, saem_list = compute_bola_da_vez_listas(hist)
        else:
            entram_list = list(entram_list_base)
            saem_list = list(saem_list_base)

        freqs = compute_number_frequencies(hist)
        groups = compute_freq_groups(freqs)

        last = dezenas_from_row(hist[-1])
        prev1 = dezenas_from_row(hist[-2])
        prev2 = dezenas_from_row(hist[-3])
        NS_to_N, N_to_A, AH_to_H = compute_mapping_sets(last, prev1, prev2)
        N_base = len(set(last) - set(prev1))
        A_base = len((set(last) & set(prev1)) - set(prev2))
        H_base = len(set(last) & set(prev1) & set(prev2))

        if aplicar_nah:
            if nah_list_provided:
                allowed_nah = set(nah_list)
            else:
                allowed_nah = set(generate_nah_variations((N_base, A_base, H_base), var_range=nah_var))
        else:
            allowed_nah = set()

        filtradas = []
        for r in bets:
            dz = dezenas_from_row(r)
            countN = sum(1 for d in dz if d in NS_to_N)
            countA = sum(1 for d in dz if d in N_to_A)
            countH = sum(1 for d in dz if d in AH_to_H)

            if aplicar_cre and count_cre(dz) >= 2:
                continue
            if aplicar_salto:
                mj = max_jump(dz)
                if mj not in (3, 4):
                    continue
            if aplicar_col:
                cols = count_columns(dz)
                if not filter_by_vector(cols, col_min, col_max):
                    continue
            if aplicar_soma:
                soma = sum(dz)
                if soma_min is not None and soma < soma_min:
                    continue
                if soma_max is not None and soma > soma_max:
                    continue
            if aplicar_nah and (countN, countA, countH) not in allowed_nah:
                continue
            if aplicar_abcd:
                cnts, _ = count_groups(dz, groups)
                if not filter_by_vector(cnts, abcd_min, abcd_max):
                    continue
            if aplicar_tres and not has_line_three_consecutives_3L(dz):
                continue
            if aplicar_bola_vez and not bola_da_vez(dz, entram_list, saem_list):
                continue
            if aplicar_losango and not in_losango_ou_centro(dz):
                continue
            if aplicar_onze_quinze and not tem_dezena_onze_ou_quinze(dz):
                continue
            if aplicar_countc_min_um_quatro and not minimo_um_quatro(dz):
                continue
            if aplicar_max_um_cinco and not maximo_um_cinco(dz):
                continue
            if aplicar_countcs and not countcs_em_valores(dz, (2, 3, 4, 5)):
                continue
            if aplicar_cantos and not filtro_cantos(dz, minimo=2):
                continue
            if aplicar_diagonais and not filtro_diagonais(dz):
                continue

            filtradas.append({
                'dezenas': dz,
                'id': r.get('concurso'),
            })

        filtered_index = {tuple(sorted(item['dezenas'])): idx + 1 for idx, item in enumerate(filtradas)}
        winner_filtered_pos = filtered_index.get(next_dezenas)
        winner_in_filtered = winner_filtered_pos is not None
        if winner_in_filtered:
            winner_in_filtered_count += 1

        mode_hits: dict[str, int | None] = {}

        for mode_idx, mode in enumerate(requested_modes):
            rng = random.Random(selection_seed + cutoff_atual * 131 + mode_idx * 17)
            if mode == 'primeiras':
                selected = _select_first(filtradas, backtest_top_n)
            elif mode == 'diversidade':
                selected = _select_diverse(filtradas, backtest_top_n, freqs, rng)
            elif mode == 'estratificada':
                selected = _select_stratified(filtradas, backtest_top_n, groups, rng)
            elif mode == 'distantes':
                selected = _select_distant(filtradas, backtest_top_n)
            else:
                selected = _select_random(filtradas, backtest_top_n, rng)

            selected_pos = None
            for pos, item in enumerate(selected, start=1):
                if tuple(sorted(item['dezenas'])) == next_dezenas:
                    selected_pos = pos
                    break

            stats = mode_stats[mode]
            stats['tests'] += 1
            stats['filtered_sum'] += len(filtradas)
            stats['selected_sum'] += len(selected)
            if selected_pos is not None:
                stats['hits'] += 1
                stats['pos_sum'] += selected_pos
                stats['pos_count'] += 1
                if stats['best_pos'] is None or selected_pos < stats['best_pos']:
                    stats['best_pos'] = selected_pos
                if stats['worst_pos'] is None or selected_pos > stats['worst_pos']:
                    stats['worst_pos'] = selected_pos

            mode_hits[mode] = selected_pos

        details.append({
            'cutoff': cutoff_atual,
            'nextConcurso': cutoff_atual + 1,
            'nextPadraoLinha': next_padrao_linha,
            'filteredTotal': len(filtradas),
            'winnerInFiltered': winner_in_filtered,
            'winnerFilteredPos': winner_filtered_pos,
            'nahBase': [N_base, A_base, H_base],
            'nahAllowedCount': len(allowed_nah) if aplicar_nah else 0,
            'bolaVezEntramUsadas': sorted(entram_list) if aplicar_bola_vez else [],
            'bolaVezSaemUsadas': sorted(saem_list) if aplicar_bola_vez else [],
            'modeHits': mode_hits,
        })

    total_avaliados = len(details)
    if total_avaliados == 0:
        return jsonify({'error': 'nao foi possivel avaliar nenhum cutoff'}), 400

    summaries = []
    for mode in requested_modes:
        stats = mode_stats[mode]
        tests = stats['tests'] or 0
        hits = stats['hits'] or 0
        pos_count = stats['pos_count'] or 0
        summaries.append({
            'mode': mode,
            'tests': tests,
            'hits': hits,
            'hitRate': (hits * 100.0 / tests) if tests else 0.0,
            'avgFilteredTotal': (stats['filtered_sum'] / tests) if tests else 0.0,
            'avgSelectedSize': (stats['selected_sum'] / tests) if tests else 0.0,
            'avgSelectedPos': (stats['pos_sum'] / pos_count) if pos_count else None,
            'bestSelectedPos': stats['best_pos'],
            'worstSelectedPos': stats['worst_pos'],
        })

    details.sort(key=lambda d: d['cutoff'], reverse=True)
    winner_rate = (winner_in_filtered_count * 100.0 / total_avaliados) if total_avaliados else 0.0

    return jsonify({
        'fromCutoff': min(item['cutoff'] for item in details),
        'toCutoff': max(item['cutoff'] for item in details),
        'padraoLinha': padrao_linha,
        'window': backtest_window,
        'step': backtest_step,
        'topN': backtest_top_n,
        'totalAvaliados': total_avaliados,
        'winnerInFilteredCount': winner_in_filtered_count,
        'winnerInFilteredRate': winner_rate,
        'modes': summaries,
        'details': details,
    })

@app.route('/api/selecionar')
def selecionar_apostas():
    """HeurÃ­stica de seleÃ§Ã£o de apostas: score + diversidade (Jaccard).

    ParÃ¢metros (query):
      - k: quantidade de apostas a selecionar (default: 50)
      - pool: tamanho do pool top-N por score para diversidade (default: 200)
      - freqJanela: janela dos Ãºltimos N concursos para frequÃªncia histÃ³rica (default: None=todo histÃ³rico)
      - weights: wFreq, wSeq3, wJump, wPar (ex.: wFreq=1.0, wSeq3=-0.7, wJump=-0.4, wPar=-0.3)
      - pares/impares: filtros opcionais iguais aos jÃ¡ usados
    """
    from filters import FiltroDezenasParesImpares
    from selector import compute_number_frequencies, score_bet, select_diverse

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

    k = request.args.get('k', default=50, type=int)
    pool = request.args.get('pool', default=200, type=int)
    freq_janela = request.args.get('freqJanela', default=None, type=int)
    w_freq = request.args.get('wFreq', default=1.0, type=float)
    w_seq3 = request.args.get('wSeq3', default=-0.7, type=float)
    w_jump = request.args.get('wJump', default=-0.4, type=float)
    w_par = request.args.get('wPar', default=-0.3, type=float)
    cutoff = request.args.get('cutoff', default=None, type=int)

    pares_param = request.args.get('pares', '')
    impares_param = request.args.get('impares', '')
    pares = _parse_int_list(request.args.getlist('pares') or [pares_param])
    impares = _parse_int_list(request.args.getlist('impares') or [impares_param])

    # Load bets (3 por linha base)
    csv_path = Path(__file__).resolve().parent.parent / 'todasTresPorLinha.csv'
    with csv_path.open(newline='') as f:
        reader = csv.DictReader(f)
        bets = []
        for idx, row in enumerate(reader, start=1):
            data_row = {f'n{i}': int(row[f'B{i}']) for i in range(1, 16)}
            data_row['concurso'] = idx
            data_row['data'] = ''
            data_row['ganhador'] = 0
            bets.append(data_row)

    # Optional parity filter
    filtro_paridade = FiltroDezenasParesImpares(pares, impares, ativo=bool(pares or impares))
    bets = filtro_paridade.apply(bets)

    total_filtrado = len(bets)

    # Historical frequencies from DB
    conn = get_connection()
    if conn is None:
        app.logger.warning('lotofacil.db not found for frequencies; using zeros')
        freqs = {i: 0 for i in range(1, 26)}
    else:
        if cutoff is not None:
            cur = conn.execute(
                'SELECT concurso, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15 FROM results WHERE concurso <= ? ORDER BY concurso ASC',
                (cutoff,)
            )
        else:
            cur = conn.execute(
                'SELECT concurso, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15 FROM results ORDER BY concurso ASC'
            )
        hist_rows = cur.fetchall()
        conn.close()
        freqs = compute_number_frequencies(hist_rows, last_n=freq_janela)

    # Score all bets
    scored = []
    for r in bets:
        dezenas = [r[f'n{i}'] for i in range(1, 16)]
        sc = score_bet(
            dezenas,
            freqs,
            w_freq=w_freq,
            w_seq3=w_seq3,
            w_jump=w_jump,
            w_par_balance=w_par,
        )
        scored.append((dezenas, sc))

    # Select diverse top-k
    selected = select_diverse(scored, k=k, greedy_pool=pool)

    # Build response
    results = []
    for dezenas, sc in selected:
        pares_q = sum(1 for d in dezenas if d % 2 == 0)
        results.append({
            'dezenas': list(sorted(dezenas)),
            'score': round(sc, 6),
            'qtdPares': pares_q,
            'qtdImpares': 15 - pares_q,
        })

    return jsonify({
        'totalFiltrado': total_filtrado,
        'selecionadas': len(results),
        'k': k,
        'pool': pool,
        'freqJanela': freq_janela,
        'cutoff': cutoff,
        'results': results,
    })

@app.route('/api/selecionar/conferir', methods=['POST', 'OPTIONS'])
def conferir_selecao():
    if request.method == 'OPTIONS':
        # Preflight CORS
        resp = app.make_default_options_response()
        return resp
    data = request.get_json(silent=True) or {}
    cutoff = data.get('cutoff')
    bets = data.get('bets') or []
    opts = data.get('options') or {}
    if not isinstance(cutoff, int):
        return jsonify({'error': 'cutoff invÃ¡lido'}), 400
    # Buscar prÃ³ximo concurso (cutoff + 1)
    conn = get_connection()
    if conn is None:
        return jsonify({'error': 'lotofacil.db not found'}), 500
    cur = conn.execute(
        'SELECT concurso, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15 FROM results WHERE concurso = ?',
        (cutoff + 1,)
    )
    row = cur.fetchone()
    # also fetch history up to cutoff for ABCD frequency groups
    cur2 = conn.execute(
        'SELECT concurso, n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, n12, n13, n14, n15 FROM results WHERE concurso <= ? ORDER BY concurso ASC',
        (cutoff,)
    )
    hist_rows = cur2.fetchall()
    conn.close()
    if row is None:
        return jsonify({'message': 'Resultado seguinte nÃ£o encontrado', 'nextConcurso': cutoff + 1, 'results': []}), 404
    next_dezenas = [row[f'n{i}'] for i in range(1, 16)]
    s_next = set(next_dezenas)
    # compute classifications
    try:
        from selector import compute_number_frequencies
        from pipeline_filters import (
            count_par_impar, max_jump, longest_consecutive_run,
            count_columns, compute_freq_groups, count_groups, dezenas_from_row,
            has_line_three_consecutives_3L, filter_by_vector,
            bola_da_vez, in_losango_ou_centro, maximo_um_cinco,
            minimo_um_quatro, tem_dezena_onze_ou_quinze, countcs_em_valores,
            filtro_cantos, filtro_diagonais, compute_bola_da_vez_listas
        )
        freqs = compute_number_frequencies(hist_rows)
        groups = compute_freq_groups(freqs)
        abcd_counts, _ = count_groups(next_dezenas, groups)
        pares, impares = count_par_impar(next_dezenas)
        # NAH for next result relative to last two (up to cutoff)
        nah_counts = None
        if len(hist_rows) >= 2:
            prev1 = dezenas_from_row(hist_rows[-1])
            prev2 = dezenas_from_row(hist_rows[-2])
            s_cur = set(next_dezenas)
            s_prev1 = set(prev1)
            s_prev2 = set(prev2)
            N = s_cur - s_prev1
            A = (s_cur & s_prev1) - s_prev2
            H = s_cur & s_prev1 & s_prev2
            nah_counts = [len(N), len(A), len(H)]
        next_info = {
            'qtdPares': pares,
            'qtdImpares': impares,
            'maiorSalto': max_jump(next_dezenas),
            'maiorConsecutivas': longest_consecutive_run(next_dezenas),
            'countC': count_columns(next_dezenas),
            'abcdCounts': abcd_counts,
            'nahCounts': nah_counts,
        }
        # filter pass/fail diagnostics (against provided options)
        def _b(name, default=False):
            v = opts.get(name)
            return bool(v) if v is not None else default
        aplicarPI = _b('aplicarPI', True)
        aplicarCRE = _b('aplicarCRE', True)
        aplicarSalto = _b('aplicarSalto', True)
        aplicarNAH = _b('aplicarNAH', True)
        aplicarABCD = _b('aplicarABCD', True)
        aplicarTres = _b('aplicarTresConsec', True)
        aplicarBolaVez = _b('aplicarBolaVez', False)
        aplicarLosango = _b('aplicarLosangoCentro', False)
        aplicarOnzeQuinze = _b('aplicarOnzeQuinze', False)
        aplicarCountCMinUmQuatro = _b('aplicarCountCMinUmQuatro', False)
        aplicarMaxUmCinco = _b('aplicarMaxUmCinco', False)
        aplicarCountCS = _b('aplicarCountCS', False)
        aplicarCantos = _b('aplicarCantos', False)
        aplicarDiagonais = _b('aplicarDiagonais', False)
        aplicarSoma = _b('aplicarSoma', False)
        colMin = opts.get('colMin') or [2,1,1,1,1]
        colMax = opts.get('colMax') or [5,5,4,5,5]
        abcdMin = opts.get('abcdMin') or [0,2,4,0]
        abcdMax = opts.get('abcdMax') or [3,8,10,5]
        somaMin = opts.get('somaMin')
        somaMax = opts.get('somaMax')
        try:
            somaMin = int(somaMin) if somaMin is not None else None
        except (TypeError, ValueError):
            somaMin = None
        try:
            somaMax = int(somaMax) if somaMax is not None else None
        except (TypeError, ValueError):
            somaMax = None
        if somaMin is not None and somaMax is not None and somaMin > somaMax:
            somaMin, somaMax = somaMax, somaMin
        nahVar = int(opts.get('nahVar') or 2)
        paresAllow = set(opts.get('pares') or [])
        imparesAllow = set(opts.get('impares') or [])
        bolaEntram = opts.get('bolaVezEntram') or []
        bolaSaem = opts.get('bolaVezSaem') or []
        if aplicarBolaVez and not bolaEntram and not bolaSaem:
            bolaEntram, bolaSaem = compute_bola_da_vez_listas(hist_rows)

        # build NAH allowed set similar to selection
        allowed_nah = set()
        if aplicarNAH and len(hist_rows) >= 3:
            last = dezenas_from_row(hist_rows[-1])
            prev1 = dezenas_from_row(hist_rows[-2])
            prev2 = dezenas_from_row(hist_rows[-3])
            N_base = len(set(last) - set(prev1))
            A_base = len((set(last) & set(prev1)) - set(prev2))
            H_base = len(set(last) & set(prev1) & set(prev2))
            from pipeline_filters import generate_nah_variations
            allowed_nah = set(generate_nah_variations((N_base, A_base, H_base), var_range=nahVar))

        # compute basic attributes for next result
        next_cols = count_columns(next_dezenas)
        abcd_ok = True
        if aplicarABCD:
            abcd_ok = filter_by_vector(abcd_counts, abcdMin, abcdMax)
        cols_ok = filter_by_vector(next_cols, colMin, colMax)
        tres_ok = has_line_three_consecutives_3L(next_dezenas) if aplicarTres else True
        pi_ok = True
        if aplicarPI and (paresAllow or imparesAllow):
            p = sum(1 for d in next_dezenas if d % 2 == 0)
            i = 15 - p
            if paresAllow and p not in paresAllow:
                pi_ok = False
            if imparesAllow and i not in imparesAllow:
                pi_ok = False
        nah_ok = True
        if aplicarNAH and nah_counts is not None:
            nah_ok = tuple(nah_counts) in allowed_nah
        bola_ok = bola_da_vez(next_dezenas, bolaEntram, bolaSaem) if aplicarBolaVez else True
        los_ok = in_losango_ou_centro(next_dezenas) if aplicarLosango else True
        onz_ok = tem_dezena_onze_ou_quinze(next_dezenas) if aplicarOnzeQuinze else True
        min4_ok = minimo_um_quatro(next_dezenas) if aplicarCountCMinUmQuatro else True
        max5_ok = maximo_um_cinco(next_dezenas) if aplicarMaxUmCinco else True
        countcs_ok = countcs_em_valores(next_dezenas, (2, 3, 4, 5)) if aplicarCountCS else True
        cantos_ok = filtro_cantos(next_dezenas, minimo=2) if aplicarCantos else True
        diagonais_ok = filtro_diagonais(next_dezenas) if aplicarDiagonais else True
        soma_ok = True
        if aplicarSoma:
            soma_total = sum(next_dezenas)
            if somaMin is not None and soma_total < somaMin:
                soma_ok = False
            if somaMax is not None and soma_total > somaMax:
                soma_ok = False
        cre_ok = True  # CRE is defined on generated bets grid-like structure; for next result we can compute pattern equality between adjacent rows
        try:
            from pipeline_filters import count_cre
            cre_ok = (count_cre(next_dezenas) < 2) if aplicarCRE else True
        except Exception:
            cre_ok = True
        salto_ok = (max_jump(next_dezenas) in (3,4)) if aplicarSalto else True

        filters_check = {
            'ParImpar': pi_ok,
            'CRE': cre_ok,
            'Salto': salto_ok,
            'Colunas': cols_ok,
            'NAH': nah_ok,
            'ABCD': abcd_ok,
            'TresConsecLinha': tres_ok,
            'BolaDaVez': bola_ok,
            'LosangoOuCentro': los_ok,
            'OnzeQuinze': onz_ok,
            'CountCMinUmQuatro': min4_ok,
            'MaximoUmCinco': max5_ok,
            'CountCS': countcs_ok,
            'Cantos': cantos_ok,
            'Diagonais': diagonais_ok,
            'SomaDezenas': soma_ok,
        }
    except Exception:
        next_info = None
        filters_check = None
    out = []
    for dz in bets:
        try:
            s_bet = set(int(x) for x in dz)
        except Exception:
            s_bet = set()
        acertos = len(s_bet & s_next)
        out.append({'dezenas': sorted(list(s_bet)), 'acertos': acertos})
    return jsonify({'nextConcurso': cutoff + 1, 'nextDezenas': next_dezenas, 'nextInfo': next_info, 'filtersCheck': filters_check, 'results': out})


@app.route('/api/dia-da-sorte/atualizar', methods=['POST'])
def update_dia_da_sorte():
    try:
        inserted = update_dia_da_sorte_results()
        count = len(inserted)
        if count:
            message = f'{count} concurso(s) atualizado(s): {", ".join(str(item) for item in inserted)}.'
        else:
            message = 'Nenhum novo concurso encontrado.'
        return jsonify({'inserted': inserted, 'count': count, 'message': message})
    except Exception as exc:
        app.logger.exception('Falha ao atualizar resultados do Dia da Sorte: %s', exc)
        return jsonify({'message': 'Falha ao atualizar resultados do Dia da Sorte.'}), 500


@app.route('/api/lotofacil/atualizar', methods=['POST'])
def update_lotofacil():
    try:
        inserted = update_lotofacil_results()
        count = len(inserted)
        if count:
            message = f'{count} concurso(s) atualizado(s): {", ".join(str(item) for item in inserted)}.'
        else:
            message = 'Nenhum novo concurso encontrado.'
        return jsonify({'inserted': inserted, 'count': count, 'message': message})
    except Exception as exc:
        app.logger.exception('Falha ao atualizar resultados da Lotofacil: %s', exc)
        return jsonify({'message': 'Falha ao atualizar resultados da Lotofacil.'}), 500

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

if __name__ == '__main__':
    app.run()








