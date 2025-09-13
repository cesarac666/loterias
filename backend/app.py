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
        generate_nah_variations, compute_mapping_sets, has_line_three_consecutives_3L
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
    aplicar_pi = _bool('aplicarPI', True)
    limit = request.args.get('limit', default=200, type=int)

    col_min = _parse_vec(request.args.get('colMin', ''), 5) or [2, 1, 1, 1, 1]
    col_max = _parse_vec(request.args.get('colMax', ''), 5) or [5, 5, 4, 5, 5]
    abcd_min = _parse_vec(request.args.get('abcdMin', ''), 4) or [0, 2, 4, 0]
    abcd_max = _parse_vec(request.args.get('abcdMax', ''), 4) or [3, 8, 10, 5]

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
            count_columns, compute_freq_groups, count_groups, dezenas_from_row
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
    except Exception:
        next_info = None
    out = []
    for dz in bets:
        try:
            s_bet = set(int(x) for x in dz)
        except Exception:
            s_bet = set()
        acertos = len(s_bet & s_next)
        out.append({'dezenas': sorted(list(s_bet)), 'acertos': acertos})
    return jsonify({'nextConcurso': cutoff + 1, 'nextDezenas': next_dezenas, 'nextInfo': next_info, 'results': out})

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == '__main__':
    app.run()
