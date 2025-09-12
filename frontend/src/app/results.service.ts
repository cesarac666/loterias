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
}

export interface ResultsResponse {
  total: number;
  results: LotofacilResult[];
}

@Injectable({
  providedIn: 'root'
})
export class ResultsService {
  private readonly API_URL = 'http://localhost:5000/api/results';
  private readonly BETS_URL = 'http://localhost:5000/api/apostas';

  constructor(private http: HttpClient) {}

  getLastResults(
    pares: number[] = [],
    impares: number[] = [],
    concursoLimite?: number,
    padraoLinha?: string
  ): Observable<ResultsResponse> {
    let params = new HttpParams();
    if (pares.length) {
      pares.forEach(p => {
        params = params.append('pares', p.toString());
      });
    }
    if (impares.length) {
      impares.forEach(i => {
        params = params.append('impares', i.toString());
      });
    }
    if (concursoLimite !== undefined) {
      params = params.set('concursoLimite', concursoLimite.toString());
    }
    if (padraoLinha) {
      params = params.set('padraoLinha', padraoLinha);
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
      pares.forEach(p => {
        params = params.append('pares', p.toString());
      });
    }
    if (impares.length) {
      impares.forEach(i => {
        params = params.append('impares', i.toString());
      });
    }
    if (concursoLimite !== undefined) {
      params = params.set('concursoLimite', concursoLimite.toString());
    }
    return this.http.get<ResultsResponse>(this.BETS_URL, { params });
  }
}
