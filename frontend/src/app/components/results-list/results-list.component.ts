import { Component, OnInit } from '@angular/core';
import { ResultsService, LotofacilResult } from '../../results.service';

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

  constructor(private resultsService: ResultsService) {}

  ngOnInit(): void {
    this.loadResults();
  }

  loadResults(): void {
    const paresVals = this.pares
      .split(',')
      .map(v => parseInt(v, 10))
      .filter(v => !isNaN(v));
    const imparesVals = this.impares
      .split(',')
      .map(v => parseInt(v, 10))
      .filter(v => !isNaN(v));
    const pares = this.useParImpar ? paresVals : [];
    const impares = this.useParImpar ? imparesVals : [];
    this.resultsService.getLastResults(pares, impares)
      .subscribe(r => this.results = r);
  }
}
