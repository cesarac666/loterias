import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface LotofacilResult {
  concurso: number;
  data: string;
  dezenas: number[];
  ganhador: number;
  qtdPares: number;
  qtdImpares: number;
  padraoLinha: string;
  nahN?: number | null;
  nahA?: number | null;
  nahH?: number | null;
}

export interface ResultsResponse {
  total: number;
  results: LotofacilResult[];
  nahTransitionCurrent?: number[] | null;
  nahTransitionSummary?: { nah: number[]; count: number }[];
  nahTransitionTotal?: number;
  nahTransitionPairs?: {
    ccCurrent: number;
    ccNext: number;
    currentNah: number[];
    nextNah: number[];
  }[];
}

export interface SelectionItem {
  dezenas: number[];
  score: number;
  qtdPares: number;
  qtdImpares: number;
  acertos?: number;
}

export interface SelectionResponse {
  totalFiltrado: number;
  selecionadas: number;
  k: number;
  pool: number;
  freqJanela: number | null;
  cutoff?: number | null;
  results: SelectionItem[];
}

export interface CheckResponseItem {
  dezenas: number[];
  acertos: number;
}

export interface CheckResponse {
  nextConcurso: number;
  nextDezenas?: number[];
  nextInfo?: {
    qtdPares: number;
    qtdImpares: number;
    maiorSalto: number;
    maiorConsecutivas: number;
    countC: number[];
    abcdCounts: number[];
    nahCounts?: number[] | null;
  } | null;
  filtersCheck?: { [name: string]: boolean } | null;
  results: CheckResponseItem[];
  message?: string;
}

export interface LotofacilSaveResponse {
  nextConcurso: number;
  totalReceived: number;
  totalValid: number;
  inserted: number;
  alreadySaved: number;
  invalid: number;
  message?: string;
}

export interface LotofacilSavedBet {
  id: number;
  concurso: number;
  dezenas: number[];
  acertos: number | null;
  acertosRegistrados: number;
  resultadoDisponivel: boolean;
  resultado: number[] | null;
  dataSorteio: string | null;
  createdAt: string;
  registradoEm?: string | null;
}

export interface LotofacilSavedResponse {
  total: number;
  results: LotofacilSavedBet[];
}

export interface LotofacilDeleteResponse {
  deleted: number;
  concurso: number | null;
}

export interface LotofacilCheckoutResponse {
  message: string;
  script?: string;
  concurso: number | null;
  limit: number | null;
  shuffle?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ResultsService {
  private readonly API_URL = 'http://localhost:5000/api/results';
  private readonly BETS_URL = 'http://localhost:5000/api/apostas';
  private readonly SELECT_URL = 'http://localhost:5000/api/selecionar';
  private readonly SELECT_FILTERS_URL = 'http://localhost:5000/api/selecionar-filtros';
  private readonly UPDATE_LOTOFACIL_URL = 'http://localhost:5000/api/lotofacil/atualizar';
  private readonly LOTO_SAVED_URL = 'http://localhost:5000/api/lotofacil/apostas/salvas';
  private readonly LOTO_SAVE_URL = 'http://localhost:5000/api/lotofacil/apostas/salvar';
  private readonly LOTO_SUBMIT_URL = 'http://localhost:5000/api/lotofacil/apostas/enviar';

  constructor(private http: HttpClient) {}

  getLastResults(
    pares: number[] = [],
    impares: number[] = [],
    concursoLimite?: number,
    padraoLinha?: string,
    nah?: [number, number, number]
  ): Observable<ResultsResponse> {
    let params = new HttpParams();
    if (pares.length) {
      params = params.set('pares', pares.join(','));
    }
    if (impares.length) {
      params = params.set('impares', impares.join(','));
    }
    if (concursoLimite !== undefined) {
      params = params.set('concursoLimite', concursoLimite.toString());
    }
    if (padraoLinha) {
      params = params.set('padraoLinha', padraoLinha);
    }
    if (nah && nah.length === 3) {
      params = params.set('nah', nah.join(','));
    }

    return this.http.get<ResultsResponse>(this.API_URL, { params });
  }

  getTresPorLinhaBets(
    pares: number[] = [],
    impares: number[] = [],
    concursoLimite?: number
  ): Observable<ResultsResponse> {
    let params = new HttpParams();
    if (pares.length) {
      params = params.set('pares', pares.join(','));
    }
    if (impares.length) {
      params = params.set('impares', impares.join(','));
    }
    if (concursoLimite !== undefined) {
      params = params.set('concursoLimite', concursoLimite.toString());
    }
    return this.http.get<ResultsResponse>(this.BETS_URL, { params });
  }

  getSelection(options: {
    k?: number;
    pool?: number;
    freqJanela?: number;
    wFreq?: number;
    wSeq3?: number;
    wJump?: number;
    wPar?: number;
    pares?: number[];
    impares?: number[];
    cutoff?: number;
  } = {}): Observable<SelectionResponse> {
    let params = new HttpParams();
    const {
      k, pool, freqJanela, wFreq, wSeq3, wJump, wPar, pares = [], impares = [], cutoff
    } = options;
    if (k !== undefined) params = params.set('k', String(k));
    if (pool !== undefined) params = params.set('pool', String(pool));
    if (freqJanela !== undefined) params = params.set('freqJanela', String(freqJanela));
    if (wFreq !== undefined) params = params.set('wFreq', String(wFreq));
    if (wSeq3 !== undefined) params = params.set('wSeq3', String(wSeq3));
    if (wJump !== undefined) params = params.set('wJump', String(wJump));
    if (wPar !== undefined) params = params.set('wPar', String(wPar));
    if (pares.length) params = params.set('pares', pares.join(','));
    if (impares.length) params = params.set('impares', impares.join(','));
    if (cutoff !== undefined) params = params.set('cutoff', String(cutoff));
    return this.http.get<SelectionResponse>(this.SELECT_URL, { params });
  }

  checkSelection(cutoff: number, bets: number[][], options?: any): Observable<CheckResponse> {
    return this.http.post<CheckResponse>(`${this.SELECT_URL}/conferir`, {
      cutoff,
      bets,
      options
    });
  }

  getFilterSelection(options: {
    cutoff: number;
    aplicarPI?: boolean;
    aplicarCRE?: boolean;
    aplicarSalto?: boolean;
    colMin?: number[];
    colMax?: number[];
    aplicarNAH?: boolean;
    nahVar?: number;
    aplicarABCD?: boolean;
    abcdMin?: number[];
    abcdMax?: number[];
    aplicarTresConsec?: boolean;
    pares?: number[];
    impares?: number[];
    limit?: number;
    selectionMode?: string;
    selectionSeed?: number;
    nahList?: string;
  }): Observable<{
    totalBase: number;
    cutoff: number;
    nahBase: [number, number, number];
    nahAllowed: [number, number, number][];
    totalFiltrado: number;
    results: { dezenas: number[]; qtdPares: number; qtdImpares: number; nahN?: number; nahA?: number; nahH?: number }[];
    nahList?: number[][];
    nahListProvided?: boolean;
    selectionMode?: string;
    selectionSeed?: number | null;
  }> {
    let params = new HttpParams();
    const {
      cutoff,
      aplicarPI,
      aplicarCRE,
      aplicarSalto,
      colMin,
      colMax,
      aplicarNAH,
      nahVar,
      aplicarABCD,
      abcdMin,
      abcdMax,
      aplicarTresConsec,
      pares = [],
      impares = [],
      limit,
      selectionMode,
      selectionSeed,
      nahList
    } = options;
    params = params.set('cutoff', String(cutoff));
    if (aplicarPI !== undefined) params = params.set('aplicarPI', String(aplicarPI));
    if (aplicarCRE !== undefined) params = params.set('aplicarCRE', String(aplicarCRE));
    if (aplicarSalto !== undefined) params = params.set('aplicarSalto', String(aplicarSalto));
    if (colMin && colMin.length === 5) params = params.set('colMin', colMin.join(','));
    if (colMax && colMax.length === 5) params = params.set('colMax', colMax.join(','));
    if (aplicarNAH !== undefined) params = params.set('aplicarNAH', String(aplicarNAH));
    if (nahVar !== undefined) params = params.set('nahVar', String(nahVar));
    if (aplicarABCD !== undefined) params = params.set('aplicarABCD', String(aplicarABCD));
    if (abcdMin && abcdMin.length === 4) params = params.set('abcdMin', abcdMin.join(','));
    if (abcdMax && abcdMax.length === 4) params = params.set('abcdMax', abcdMax.join(','));
    if (aplicarTresConsec !== undefined) params = params.set('aplicarTresConsec', String(aplicarTresConsec));
    if (pares.length) params = params.set('pares', pares.join(','));
    if (impares.length) params = params.set('impares', impares.join(','));
    if (limit !== undefined) params = params.set('limit', String(limit));
    if (selectionMode) params = params.set('selectionMode', selectionMode);
    if (selectionSeed !== undefined) params = params.set('selectionSeed', String(selectionSeed));
    if (nahList) params = params.set('nahList', nahList);
    return this.http.get<any>(this.SELECT_FILTERS_URL, { params });
  }

  updateLotofacilResults(): Observable<{ inserted: number[]; count: number; message: string }> {
    return this.http.post<{ inserted: number[]; count: number; message: string }>(
      this.UPDATE_LOTOFACIL_URL,
      {}
    );
  }

  saveLotofacilBets(cutoff: number, bets: number[][]): Observable<LotofacilSaveResponse> {
    return this.http.post<LotofacilSaveResponse>(this.LOTO_SAVE_URL, { cutoff, bets });
  }

  getSavedLotofacilBets(concurso?: number): Observable<LotofacilSavedResponse> {
    let params = new HttpParams();
    if (concurso !== undefined && concurso !== null) {
      params = params.set('concurso', String(concurso));
    }
    return this.http.get<LotofacilSavedResponse>(this.LOTO_SAVED_URL, { params });
  }

  deleteSavedLotofacilBets(concurso?: number): Observable<LotofacilDeleteResponse> {
    let params = new HttpParams();
    if (concurso !== undefined && concurso !== null) {
      params = params.set('concurso', String(concurso));
    }
    return this.http.delete<LotofacilDeleteResponse>(this.LOTO_SAVED_URL, { params });
  }

  submitSavedLotofacilBets(concurso?: number, limit?: number, shuffle: boolean = true): Observable<LotofacilCheckoutResponse> {
    const body: any = { concurso: concurso ?? null };
    if (typeof limit === 'number' && Number.isFinite(limit) && limit > 0) {
      body.limit = Math.floor(limit);
      body.shuffle = !!shuffle;
    } else if (shuffle) {
      body.shuffle = true;
    }
    return this.http.post<LotofacilCheckoutResponse>(this.LOTO_SUBMIT_URL, body);
  }
}
