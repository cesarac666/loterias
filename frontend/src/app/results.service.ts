import { Injectable } from '@angular/core';

import { HttpClient, HttpParams } from '@angular/common/http';

import { Observable } from 'rxjs';

export interface LotofacilResult {
  concurso: number;
  data: string;
  dezenas: number[];
  ganhador: number;
}

@Injectable({
  providedIn: 'root'
})
export class ResultsService {
  private readonly API_URL = 'http://localhost:5000/api/results';

  constructor(private http: HttpClient) {}

  getLastResults(pares: number[] = [], impares: number[] = []): Observable<LotofacilResult[]> {
    let params = new HttpParams();
    if (pares.length) {
      params = params.set('pares', pares.join(','));
    }
    if (impares.length) {
      params = params.set('impares', impares.join(','));
    }
    return this.http.get<LotofacilResult[]>(this.API_URL, { params });
  }
}
