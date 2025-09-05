import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface LotofacilResult {
  concurso: number;
  data: string;
  dezenas: number[];
  ganhador: number;
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
    tresPorLinha = false,
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
    if (tresPorLinha) {
      params = params.set('tresPorLinha', 'true');
    }
    if (concursoLimite !== undefined) {
      params = params.set('concursoLimite', concursoLimite.toString());
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
