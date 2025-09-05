import { Component, OnInit } from '@angular/core';
import { ResultsService, LotofacilResult, ResultsResponse } from '../../results.service';

@Component({
  selector: 'app-results-list',
  templateUrl: './results-list.component.html',
  styleUrls: ['./results-list.component.css']
})
export class ResultsListComponent implements OnInit {
  results: LotofacilResult[] = [];
  useParImpar = false;
  pares = '';
  impares = '';
  concursoLimite = '';
  totalRegistros = 0;

  constructor(private resultsService: ResultsService) {}

  ngOnInit(): void {
    this.loadResults();
  }

  loadResults(): void {
    const paresVals = this.pares
      .replace(/;/g, ',')
      .split(',')
      .map(v => parseInt(v.trim(), 10))
      .filter(v => !isNaN(v));
    const imparesVals = this.impares
      .replace(/;/g, ',')
      .split(',')
      .map(v => parseInt(v.trim(), 10))
      .filter(v => !isNaN(v));
    const pares = this.useParImpar ? paresVals : [];
    const impares = this.useParImpar ? imparesVals : [];
    const limiteVal = parseInt(this.concursoLimite, 10);
    const limite = isNaN(limiteVal) ? undefined : limiteVal;
    this.resultsService
      .getLastResults(pares, impares, limite)
      .subscribe((r: ResultsResponse) => {
        this.results = r.results;
        this.totalRegistros = r.total;
      });
  }
}
