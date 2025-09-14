import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class StartService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getLoadData(): Observable<any[]> {
    console.log('Chamou o serviço ultimo resultado do backend py.');
    return this.http.get<any[]>(`${environment.apiUrl}/start`);
  }

  getMensagem(): Observable<any> {
    return this.http.get(this.apiUrl + '/start', { responseType: 'text' });
  }
}

export class HelloxService {}
