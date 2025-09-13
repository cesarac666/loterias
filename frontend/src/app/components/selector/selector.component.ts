import { Component } from '@angular/core';
import { ResultsService, SelectionItem, SelectionResponse } from '../../results.service';

@Component({
  selector: 'app-selector',
  templateUrl: './selector.component.html',
  styleUrls: ['./selector.component.css']
})
export class SelectorComponent {
  // Params
  k = 50;
  pool = 200;
  freqJanela = '';
  wFreq = 1.0;
  wSeq3 = -0.7;
  wJump = -0.4;
  wPar = -0.3;
  cutoff = '';

  useParImpar = false;
  pares = '';
  impares = '';

  // Results
  totalFiltrado = 0;
  selecionadas = 0;
  items: SelectionItem[] = [];
  nextConcurso?: number;
  nextDezenas: number[] = [];
  loading = false;

  constructor(private resultsService: ResultsService) {}

  runSelection(): void {
    const freqVal = parseInt(this.freqJanela, 10);
    const freq = isNaN(freqVal) ? undefined : freqVal;
    const cutoffVal = parseInt(this.cutoff, 10);
    const cutoff = isNaN(cutoffVal) ? undefined : cutoffVal;
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

    this.loading = true;
    this.resultsService.getSelection({
      k: this.k,
      pool: this.pool,
      freqJanela: freq,
      wFreq: this.wFreq,
      wSeq3: this.wSeq3,
      wJump: this.wJump,
      wPar: this.wPar,
      cutoff,
      pares,
      impares,
    }).subscribe((r: SelectionResponse) => {
      this.totalFiltrado = r.totalFiltrado;
      this.selecionadas = r.selecionadas;
      this.items = r.results;
      this.nextConcurso = undefined;
      this.nextDezenas = [];
      this.loading = false;
    }, _ => {
      this.loading = false;
    });
  }

  checkResults(): void {
    const cutoffVal = parseInt(this.cutoff, 10);
    if (isNaN(cutoffVal) || this.items.length === 0) {
      return;
    }
    const bets = this.items.map(it => it.dezenas);
    this.loading = true;
    this.resultsService.checkSelection(cutoffVal, bets).subscribe(res => {
      this.nextConcurso = res.nextConcurso;
      this.nextDezenas = res.nextDezenas || [];
      const acertosMap = new Map<string, number>();
      res.results.forEach(r => acertosMap.set(r.dezenas.join(','), r.acertos));
      this.items = this.items.map(it => ({
        ...it,
        acertos: acertosMap.get(it.dezenas.join(',')) ?? it.acertos
      }));
      this.loading = false;
    }, _ => {
      this.loading = false;
    });
  }
}
