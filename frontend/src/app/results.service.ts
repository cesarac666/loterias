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
  results: CheckResponseItem[];
  message?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ResultsService {
  private readonly API_URL = 'http://localhost:5000/api/results';
  private readonly BETS_URL = 'http://localhost:5000/api/apostas';
  private readonly SELECT_URL = 'http://localhost:5000/api/selecionar';
  private readonly SELECT_FILTERS_URL = 'http://localhost:5000/api/selecionar-filtros';

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

  checkSelection(cutoff: number, bets: number[][]): Observable<CheckResponse> {
    return this.http.post<CheckResponse>(`${this.SELECT_URL}/conferir`, {
      cutoff,
      bets
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
  }): Observable<{
    totalBase: number;
    cutoff: number;
    nahBase: [number, number, number];
    nahAllowed: [number, number, number][];
    totalFiltrado: number;
    results: { dezenas: number[]; qtdPares: number; qtdImpares: number }[];
  }> {
    let params = new HttpParams();
    const {
      cutoff, aplicarPI, aplicarCRE, aplicarSalto, colMin, colMax, aplicarNAH, nahVar,
      aplicarABCD, abcdMin, abcdMax, aplicarTresConsec, pares = [], impares = [], limit
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
    return this.http.get<any>(this.SELECT_FILTERS_URL, { params });
  }
}
