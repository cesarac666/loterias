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
  padraoLinhaLinha2 = '';
  padraoLinhaLinha5 = '';
  concursoLimite = '';
  somaMin = '';
  somaMax = '';
  nahN = '';
  nahA = '';
  nahH = '';
  abcdG1 = '';
  abcdG2 = '';
  abcdG3 = '';
  abcdG4 = '';
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
  abcdTransitionCurrent: number[] | null = null;
  abcdTransitionSummary: { abcd: number[]; count: number }[] = [];
  abcdTransitionTotal = 0;
  abcdTransitionPairs: { ccCurrent: number; ccNext: number; currentAbcd: number[]; nextAbcd: number[] }[] = [];
  abcdTransitionLimit = 22;
  abcdTransitionPairsLimit = 50;
  abcdFrequencyCutoff:
    | { cutoffSolicitado?: number | null; cutoffUsado?: number | null; totalHistorico: number; grupos: { G1: number[]; G2: number[]; G3: number[]; G4: number[] } }
    | null = null;
  abcdFrequencyRows: { numero: number; frequencia: number; grupo: string }[] = [];
  showAbcdAuditModal = false;
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

  applyFilters(event?: Event): void {
    event?.preventDefault();
    this.loadResults();
  }

  applyNahHistory(event?: Event): void {
    event?.preventDefault();
    this.loadResults();
  }

  applyAbcdHistory(event?: Event): void {
    event?.preventDefault();
    this.loadResults();
  }

  openAbcdAuditModal(): void {
    if (!this.abcdFrequencyRows.length) {
      return;
    }
    this.showAbcdAuditModal = true;
  }

  closeAbcdAuditModal(): void {
    this.showAbcdAuditModal = false;
  }

  onPadraoLinhaChange(): void {
    if (this.padraoLinha !== 'quase 3 por linha') {
      this.padraoLinhaLinha2 = '';
    }
    if (this.padraoLinha !== '1 linha completa') {
      this.padraoLinhaLinha5 = '';
    }
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
    const somaMinVal = parseInt(this.somaMin, 10);
    const somaMaxVal = parseInt(this.somaMax, 10);
    const somaMin = isNaN(somaMinVal) ? undefined : somaMinVal;
    const somaMax = isNaN(somaMaxVal) ? undefined : somaMaxVal;
    const nVal = parseInt(this.nahN, 10);
    const aVal = parseInt(this.nahA, 10);
    const hVal = parseInt(this.nahH, 10);
    const g1Val = parseInt(this.abcdG1, 10);
    const g2Val = parseInt(this.abcdG2, 10);
    const g3Val = parseInt(this.abcdG3, 10);
    const g4Val = parseInt(this.abcdG4, 10);
    const linha2Val = parseInt(this.padraoLinhaLinha2, 10);
    const linha5Val = parseInt(this.padraoLinhaLinha5, 10);
    const padraoLinhaLinha2 = isNaN(linha2Val) ? undefined : linha2Val;
    const padraoLinhaLinha5 = isNaN(linha5Val) ? undefined : linha5Val;
    const nah = !isNaN(nVal) && !isNaN(aVal) && !isNaN(hVal) ? [nVal, aVal, hVal] as [number, number, number] : undefined;
    const abcd = !isNaN(g1Val) && !isNaN(g2Val) && !isNaN(g3Val) && !isNaN(g4Val)
      ? [g1Val, g2Val, g3Val, g4Val] as [number, number, number, number]
      : undefined;
    this.resultsService
      .getLastResults(pares, impares, limite, this.padraoLinha, padraoLinhaLinha2, padraoLinhaLinha5, nah, abcd, somaMin, somaMax)
      .subscribe((r: ResultsResponse) => {
        this.chartResults = r.results;
        const cnt = Math.max(1, Number(this.displayCount) || 10);
        this.results = r.results.slice(0, cnt);

        this.totalRegistros = r.total;
        this.nahTransitionCurrent = r.nahTransitionCurrent ?? null;
        this.nahTransitionSummary = r.nahTransitionSummary || [];
        this.nahTransitionTotal = r.nahTransitionTotal || 0;
        this.nahTransitionPairs = r.nahTransitionPairs || [];
        this.abcdTransitionCurrent = r.abcdTransitionCurrent ?? null;
        this.abcdTransitionSummary = r.abcdTransitionSummary || [];
        this.abcdTransitionTotal = r.abcdTransitionTotal || 0;
        this.abcdTransitionPairs = r.abcdTransitionPairs || [];
        this.abcdFrequencyCutoff = r.abcdFrequencyCutoff ?? null;
        this.abcdFrequencyRows = r.abcdFrequencyRows || [];
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
