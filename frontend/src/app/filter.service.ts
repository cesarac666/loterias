import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class FilterService {
  constructor(private http: HttpClient) {}

  applyFilters(dataset: string, filters: string[]): Observable<any> {
    return this.http.post('/api/apply-filters', { dataset, filters });
  }
}
