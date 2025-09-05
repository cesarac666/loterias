import { Component, OnInit } from '@angular/core';
import { ResultsService, LotofacilResult, ResultsResponse } from '../../results.service';

@Component({
  selector: 'app-tres-por-linha-list',
  templateUrl: './tres-por-linha-list.component.html',
  styleUrls: ['./tres-por-linha-list.component.css']
})
export class TresPorLinhaListComponent implements OnInit {
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
      .getTresPorLinhaBets(pares, impares, limite)
      .subscribe((r: ResultsResponse) => {
        this.results = r.results;
        this.totalRegistros = r.total;
      });
  }
}
