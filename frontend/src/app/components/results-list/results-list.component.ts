import { Component, OnInit, AfterViewInit, ElementRef, ViewChild } from '@angular/core';

import { ResultsService, LotofacilResult, ResultsResponse } from '../../results.service';
import { drawChart } from '../../draw-chart';

@Component({
  selector: 'app-results-list',
  templateUrl: './results-list.component.html',
  styleUrls: ['./results-list.component.css']
})
export class ResultsListComponent implements OnInit, AfterViewInit {
  results: LotofacilResult[] = [];
  chartResults: LotofacilResult[] = [];
  useParImpar = false;
  pares = '';
  impares = '';
  padraoLinha = '';
  concursoLimite = '';
  totalRegistros = 0;
  @ViewChild('patternChart') patternChartCanvas?: ElementRef<HTMLCanvasElement>;


  constructor(private resultsService: ResultsService) {}

  ngOnInit(): void {
    this.loadResults();
  }

  ngAfterViewInit(): void {
    this.renderChart();
  }

  loadResults(): void {
    const paresVals = this.pares
      .replace(/;/g, ',')
      .split(',')
      .map(v => parseInt(v.trim(), 100))
      .filter(v => !isNaN(v));
    const imparesVals = this.impares
      .replace(/;/g, ',')
      .split(',')
      .map(v => parseInt(v.trim(), 100))
      .filter(v => !isNaN(v));
    const pares = this.useParImpar ? paresVals : [];
    const impares = this.useParImpar ? imparesVals : [];
    const limiteVal = parseInt(this.concursoLimite, 100);
    const limite = isNaN(limiteVal) ? undefined : limiteVal;
    this.resultsService
      .getLastResults(pares, impares, limite, this.padraoLinha)
      .subscribe((r: ResultsResponse) => {
        this.chartResults = r.results;
        this.results = r.results.slice(0, 100);
        this.totalRegistros = r.total;
        this.renderChart();
      });
  }

  renderChart(): void {
    const canvas = this.patternChartCanvas?.nativeElement;
    if (!canvas) {
      return;
    }
    drawChart(canvas, this.results);
  }

}
