// src/app/dados.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class HelloxService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  getMensagem(): Observable<any> {
    return this.http.get(this.apiUrl + '/hello', { responseType: 'text' }); // , { responseType: 'text' }
    // return new Observable();
  }
}
