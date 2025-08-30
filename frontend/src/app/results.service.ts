import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
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

  getLastResults(): Observable<LotofacilResult[]> {
    return this.http.get<LotofacilResult[]>(this.API_URL);
  }
}
