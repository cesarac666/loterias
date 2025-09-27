import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface DigitStats {
  units: Record<string, number>;
  tens: Record<string, number>;
}

export interface DiaDaSorteResult {
  concurso: number;
  dataSorteio: string;
  bolas: number[];
  mesDaSorte: number;
  ganhadores7Acertos: number;
  pares: number;
  impares: number;
  nahN: number | null;
  nahA: number | null;
  nahH: number | null;
  maxConsec: number;
  maiorSalto: number;
  isolatedCount: number;
  qdls: number[];
  digitStats: DigitStats;
}

export interface DiaDaSorteBet {
  dezenas: number[];
  pares: number;
  impares: number;
  maxConsec: number;
  maiorSalto: number;
  isolatedCount: number;
  nahN: number | null;
  nahA: number | null;
  nahH: number | null;
  qdls: number[];
  digitStats: DigitStats;
}

export interface DiaDaSorteResponse {
  total: number;
  results: DiaDaSorteResult[];
}

export interface DiaDaSorteBetsResponse {
  total: number;
  limit: number;
  offset: number;
  results: DiaDaSorteBet[];
}

@Injectable({ providedIn: 'root' })
export class DiaDaSorteService {
  private readonly API_BASE = 'http://localhost:5000/api/dia-da-sorte';

  constructor(private http: HttpClient) {}

  getResults(limit?: number): Observable<DiaDaSorteResponse> {
    let params = new HttpParams();
    if (limit !== undefined) {
      params = params.set('limit', String(limit));
    }
    return this.http.get<DiaDaSorteResponse>(this.API_BASE, { params });
  }

  filterBets(filters: any): Observable<DiaDaSorteBetsResponse> {
    return this.http.post<DiaDaSorteBetsResponse>(`${this.API_BASE}/apostas/filtrar`, filters ?? {});
  }
}
