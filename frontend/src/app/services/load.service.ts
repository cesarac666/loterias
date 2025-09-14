// src/app/dados.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class LoadService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  //getLoadData(): Observable<any[]> {
  // Mantém genericamente como any[]
  //return this.http.get<any[]>(`${environment.apiUrl}/load`);
  //}

  getLoadData(numero: number): Observable<any[]> {
    console.log('Chamou o serviço load do backend py.');
    return this.http.get<any[]>(`${environment.apiUrl}/load/${numero}`);
  }
}
