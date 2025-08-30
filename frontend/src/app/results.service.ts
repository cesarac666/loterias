import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';

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
  constructor(private http: HttpClient) {}

  getLastResults(): Observable<LotofacilResult[]> {
    return this.http.get('assets/ultimos500_lotofacil_05062023.csv', { responseType: 'text' })
      .pipe(
        map(csv => {
          const lines = csv.trim().split('\n').slice(1);
          const last10 = lines.slice(-10);
          return last10.map(line => {
            const parts = line.split(',');
            const concurso = +parts[0];
            const data = parts[1];
            const dezenas = parts.slice(2, 17).map(n => +n);
            const ganhador = +parts[17];
            return { concurso, data, dezenas, ganhador } as LotofacilResult;
          }).reverse();
        })
      );
  }
}

