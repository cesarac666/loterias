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
  nahN = '';
  nahA = '';
  nahH = '';
  displayCount = 10;
  totalRegistros = 0;
  updating = false;
  updateMessage = '';
  updateError = '';
  nahTransitionCurrent: number[] | null = null;
  nahTransitionSummary: { nah: number[]; count: number }[] = [];
  nahTransitionTotal = 0;
  nahTransitionPairs: { ccCurrent: number; ccNext: number; currentNah: number[]; nextNah: number[] }[] = [];
  nahTransitionLimit = 22;
  nahTransitionPairsLimit = 50;
  @ViewChild('patternChart') patternChartCanvas?: ElementRef<HTMLCanvasElement>;
  selectedTicketNumbers: number[] | null = null;
  showPrintPreview = false;


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
    const nVal = parseInt(this.nahN, 10);
    const aVal = parseInt(this.nahA, 10);
    const hVal = parseInt(this.nahH, 10);
    const nah = !isNaN(nVal) && !isNaN(aVal) && !isNaN(hVal) ? [nVal, aVal, hVal] as [number, number, number] : undefined;
    this.resultsService
      .getLastResults(pares, impares, limite, this.padraoLinha, nah)
      .subscribe((r: ResultsResponse) => {
        this.chartResults = r.results;
        const cnt = Math.max(1, Number(this.displayCount) || 10);
        this.results = r.results.slice(0, cnt);

        this.totalRegistros = r.total;
        this.nahTransitionCurrent = r.nahTransitionCurrent ?? null;
        this.nahTransitionSummary = r.nahTransitionSummary || [];
        this.nahTransitionTotal = r.nahTransitionTotal || 0;
        this.nahTransitionPairs = r.nahTransitionPairs || [];
        this.renderChart();
      });
  }

  renderChart(): void {
    const canvas = this.patternChartCanvas?.nativeElement;
    if (!canvas) {
      return;
    }
    drawChart(canvas, this.chartResults);
  }

  showTicket(dezenas: number[]): void {
    this.selectedTicketNumbers = dezenas;
  }

  printTicket(): void {
    window.print();
  }

  openPrintPreview(): void {
    this.showPrintPreview = true;
  }

  closePrintPreview(): void {
    this.showPrintPreview = false;
  }

  printAll(): void {
    window.print();
  }

  updateResults(): void {
    if (this.updating) {
      return;
    }
    this.updating = true;
    this.updateMessage = 'Atualizando resultados...';
    this.updateError = '';
    this.resultsService.updateLotofacilResults().subscribe({
      next: (res) => {
        this.updateMessage = res.message;
        this.updating = false;
        if (res.count > 0) {
          this.loadResults();
        }
      },
      error: () => {
        this.updateError = 'Falha ao atualizar resultados da Lotofácil.';
        this.updateMessage = '';
        this.updating = false;
      }
    });
  }

}
