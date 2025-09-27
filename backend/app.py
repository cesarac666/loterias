from flask import Flask, jsonify, request
import sqlite3
import json 
import csv
from pathlib import Path

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / 'database' / 'lotofacil.db'

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
        total = cur.execute(
            'SELECT COUNT(*) FROM dia_da_sorte_results'
        ).fetchone()[0]
        limit = request.args.get('limit', type=int)
        query = '''
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
        params = ()
        if limit and limit > 0:
            query += ' LIMIT ?'
            params = (limit,)
        rows = cur.execute(query, params).fetchall()

        def _safe_json_loads(value, fallback):
            if not value:
                return fallback
            try:
                return json.loads(value)
            except (TypeError, json.JSONDecodeError):
                return fallback

        results = [
            {
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
            }
            for row in rows
        ]
        return jsonify({'total': total, 'results': results})
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

        def _add_range(min_val, max_val, column, conditions, params):
            if min_val is not None:
                conditions.append(f"{column} >= ?")
                params.append(int(min_val))
            if max_val is not None:
                conditions.append(f"{column} <= ?")
                params.append(int(max_val))

        conditions: list[str] = []
        params: list[int] = []

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
            _add_range(data.get(min_key), data.get(max_key), column, conditions, params)

        qdls_min = data.get('qdlsMin') or []
        qdls_max = data.get('qdlsMax') or []
        for idx in range(5):
            col = f'qdls_s{idx + 1}'
            _add_range(
                qdls_min[idx] if idx < len(qdls_min) else None,
                qdls_max[idx] if idx < len(qdls_max) else None,
                col,
                conditions,
                params,
            )

        units_min = data.get('unitsMin') or []
        units_max = data.get('unitsMax') or []
        for idx in range(10):
            col = f'unit_{idx}'
            _add_range(
                units_min[idx] if idx < len(units_min) else None,
                units_max[idx] if idx < len(units_max) else None,
                col,
                conditions,
                params,
            )

        tens_min = data.get('tensMin') or []
        tens_max = data.get('tensMax') or []
        for idx in range(4):
            col = f'ten_{idx}'
            _add_range(
                tens_min[idx] if idx < len(tens_min) else None,
                tens_max[idx] if idx < len(tens_max) else None,
                col,
                conditions,
                params,
            )

        where_clause = ''
        if conditions:
            where_clause = 'WHERE ' + ' AND '.join(conditions)

        limit = int(data.get('limit') or 100)
        limit = max(1, min(limit, 1000))
        offset = int(data.get('offset') or 0)
        offset = max(0, offset)

        params_tuple = tuple(params)
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
    # Default Par/Ímpar as in notebook if none provided
    if not pares and not impares:
        pares = {6, 7, 8}
        impares = {7, 8, 9}
    concurso_limite = request.args.get('concursoLimite', type=int)
    padrao_linha = request.args.get('padraoLinha')
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

        results.append({
            'concurso': r['concurso'],
            'data': r['data'],
            'dezenas': dezenas,
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

    Parâmetros (query):
      - cutoff: concurso base (usa histórico até ele e calcula NAH para ele)
      - aplicarCRE (bool, default true): aplica countCRE < 2
      - aplicarSalto (bool, default true): aplica maiorSalto in [3,4]
      - colMin, colMax: vetores de 5 inteiros (ex: "2,1,1,1,1" e "5,5,4,5,5")
      - aplicarNAH (bool, default true): usa variações em torno do NAH base
      - nahVar (int, default 2): variação +- para N/A/H
      - aplicarABCD (bool, default true): usa combFreq com min/max defaults
      - abcdMin, abcdMax: vetores de 4 inteiros
      - aplicarNo3Consec (bool, default true): remove apostas com sequências de 3+
      - pares, impares: filtros opcionais (contagem permitida)
      - limit: máximo de apostas retornadas (default 200)
    """
    from filters import FiltroDezenasParesImpares
    from selector import compute_number_frequencies
    from pipeline_filters import (
        dezenas_from_row, count_par_impar, max_jump, count_columns, count_cre,
        has_run_len_at_least, filter_by_vector, compute_freq_groups, count_groups,
        generate_nah_variations, compute_mapping_sets, has_line_three_consecutives_3L,
        uma_bola_de_cada_vez, in_losango_ou_centro, count_in_range, maximo_um_cinco
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

    def _bool(name: str, default: bool) -> bool:
        v = request.args.get(name)
        if v is None:
            return default
        return v.lower() in ('1', 'true', 'sim', 'yes', 'y')

    cutoff = request.args.get('cutoff', type=int)
    aplicar_cre = _bool('aplicarCRE', True)
    aplicar_salto = _bool('aplicarSalto', True)
    aplicar_col = True
    aplicar_nah = _bool('aplicarNAH', True)
    nah_var = request.args.get('nahVar', default=2, type=int)
    aplicar_abcd = _bool('aplicarABCD', True)
    aplicar_tres = _bool('aplicarTresConsec', True)
    # new filters 7–11
    aplicar_bola_vez = _bool('aplicarBolaVez', False)
    aplicar_losango = _bool('aplicarLosangoCentro', False)
    aplicar_onze_quinze = _bool('aplicarOnzeQuinze', False)
    min_onze_quinze = request.args.get('minOnzeQuinze', default=2, type=int)
    aplicar_max_um_cinco = _bool('aplicarMaxUmCinco', False)
    aplicar_pi = _bool('aplicarPI', True)
    limit = request.args.get('limit', default=200, type=int)

    col_min = _parse_vec(request.args.get('colMin', ''), 5) or [2, 1, 1, 1, 1]
    col_max = _parse_vec(request.args.get('colMax', ''), 5) or [5, 5, 4, 5, 5]
    abcd_min = _parse_vec(request.args.get('abcdMin', ''), 4) or [0, 2, 4, 0]
    abcd_max = _parse_vec(request.args.get('abcdMax', ''), 4) or [3, 8, 10, 5]
    # bola-vez lists
    entram_list = _parse_vec(request.args.get('bolaVezEntram', ''), 0) or []
    saem_list = _parse_vec(request.args.get('bolaVezSaem', ''), 0) or []
    # fallback manual parse for arbitrary length
    if not entram_list:
        ent = request.args.get('bolaVezEntram', '')
        if ent:
            try:
                entram_list = [int(x.strip()) for x in ent.split(',') if x.strip()]
            except Exception:
                entram_list = []
    if not saem_list:
        sai = request.args.get('bolaVezSaem', '')
        if sai:
            try:
                saem_list = [int(x.strip()) for x in sai.split(',') if x.strip()]
            except Exception:
                saem_list = []

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
        return jsonify({'error': 'histórico insuficiente para NAH'}), 400

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
    allowed_nah = set(generate_nah_variations(nah_base, var_range=nah_var)) if aplicar_nah else set()

    # Apply pipeline filters
    filtradas = []
    for r in bets:
        dz = dezenas_from_row(r)
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
        # step NAH
        if aplicar_nah:
            countN = sum(1 for d in dz if d in NS_to_N)
            countA = sum(1 for d in dz if d in N_to_A)
            countH = sum(1 for d in dz if d in AH_to_H)
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
        # step 7) uma bola de cada vez (list-based include/exclude)
        if aplicar_bola_vez:
            if not uma_bola_de_cada_vez(dz, entram_list, saem_list):
                continue
        # step 8) losango ou centro
        if aplicar_losango:
            if not in_losango_ou_centro(dz):
                continue
        # step 9) onze-quinze (at least min)
        if aplicar_onze_quinze:
            if count_in_range(dz, 11, 15) < min_onze_quinze:
                continue
        # step 11) maximo um cinco (5th column values)
        if aplicar_max_um_cinco:
            if not maximo_um_cinco(dz):
                continue
        filtradas.append({'dezenas': dz})

    return jsonify({
        'totalBase': len(bets),
        'cutoff': cutoff,
        'nahBase': nah_base,
        'nahAllowed': sorted(list(allowed_nah)) if aplicar_nah else [],
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
        'minOnzeQuinze': min_onze_quinze,
        'aplicarMaxUmCinco': aplicar_max_um_cinco,
        'aplicarPI': aplicar_pi,
        'results': [
            {
                'dezenas': sorted(item['dezenas']),
                'qtdPares': count_par_impar(item['dezenas'])[0],
                'qtdImpares': 15 - count_par_impar(item['dezenas'])[0]
            }
            for item in filtradas[:limit]
        ],
        'totalFiltrado': len(filtradas),
        'limit': limit,
    })

@app.route('/api/selecionar')
def selecionar_apostas():
    """Heurística de seleção de apostas: score + diversidade (Jaccard).

    Parâmetros (query):
      - k: quantidade de apostas a selecionar (default: 50)
      - pool: tamanho do pool top-N por score para diversidade (default: 200)
      - freqJanela: janela dos últimos N concursos para frequência histórica (default: None=todo histórico)
      - weights: wFreq, wSeq3, wJump, wPar (ex.: wFreq=1.0, wSeq3=-0.7, wJump=-0.4, wPar=-0.3)
      - pares/impares: filtros opcionais iguais aos já usados
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
        return jsonify({'error': 'cutoff inválido'}), 400
    # Buscar próximo concurso (cutoff + 1)
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
        return jsonify({'message': 'Resultado seguinte não encontrado', 'nextConcurso': cutoff + 1, 'results': []}), 404
    next_dezenas = [row[f'n{i}'] for i in range(1, 16)]
    s_next = set(next_dezenas)
    # compute classifications
    try:
        from selector import compute_number_frequencies
        from pipeline_filters import (
            count_par_impar, max_jump, longest_consecutive_run,
            count_columns, compute_freq_groups, count_groups, dezenas_from_row,
            has_line_three_consecutives_3L, filter_by_vector,
            uma_bola_de_cada_vez, in_losango_ou_centro, count_in_range, maximo_um_cinco
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
        aplicarMaxUmCinco = _b('aplicarMaxUmCinco', False)
        colMin = opts.get('colMin') or [2,1,1,1,1]
        colMax = opts.get('colMax') or [5,5,4,5,5]
        abcdMin = opts.get('abcdMin') or [0,2,4,0]
        abcdMax = opts.get('abcdMax') or [3,8,10,5]
        nahVar = int(opts.get('nahVar') or 2)
        paresAllow = set(opts.get('pares') or [])
        imparesAllow = set(opts.get('impares') or [])
        bolaEntram = opts.get('bolaVezEntram') or []
        bolaSaem = opts.get('bolaVezSaem') or []

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
        bola_ok = uma_bola_de_cada_vez(next_dezenas, bolaEntram, bolaSaem) if aplicarBolaVez else True
        los_ok = in_losango_ou_centro(next_dezenas) if aplicarLosango else True
        onz_ok = (count_in_range(next_dezenas, 11, 15) >= int(opts.get('minOnzeQuinze') or 2)) if aplicarOnzeQuinze else True
        max5_ok = maximo_um_cinco(next_dezenas) if aplicarMaxUmCinco else True
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
            'BolaUmaVez': bola_ok,
            'LosangoOuCentro': los_ok,
            'OnzeQuinze': onz_ok,
            'MaximoUmCinco': max5_ok,
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

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == '__main__':
    app.run()







