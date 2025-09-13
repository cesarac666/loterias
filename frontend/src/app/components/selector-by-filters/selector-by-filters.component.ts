import { Component } from '@angular/core';
import { ResultsService } from '../../results.service';

@Component({
  selector: 'app-selector-by-filters',
  templateUrl: './selector-by-filters2.component.html',
  styleUrls: ['./selector-by-filters.component.css']
})
export class SelectorByFiltersComponent {
  // Inputs
  cutoff = '';
  aplicarCRE = true;
  aplicarSalto = true;
  aplicarNAH = true;
  nahVar = 2;
  aplicarABCD = true;
  aplicarTresConsec = true;
  colMin = '2,1,1,1,1';
  colMax = '5,5,4,5,5';
  abcdMin = '0,2,4,0';
  abcdMax = '3,8,10,5';
  useParImpar = true;
  pares = '6,7,8';
  impares = '7,8,9';
  limit = 200;

  // Outputs
  totalBase = 0;
  totalFiltrado = 0;
  nahBase: [number, number, number] | null = null;
  nahAllowed: [number, number, number][] = [];
  nahAllowedTooltip = '';
  items: { dezenas: number[]; qtdPares: number; qtdImpares: number; acertos?: number }[] = [];
  nextConcurso?: number;
  nextDezenas: number[] = [];
  nextInfo?: { qtdPares: number; qtdImpares: number; maiorSalto: number; maiorConsecutivas: number; countC: number[]; abcdCounts: number[] } | null;
  loading = false;

  constructor(private resultsService: ResultsService) {}

  run(): void {
    const cutoffVal = parseInt(this.cutoff, 10);
    if (isNaN(cutoffVal)) return;
    const paresVals = this.pares.replace(/;/g, ',').split(',').map(v => parseInt(v.trim(), 10)).filter(v => !isNaN(v));
    const imparesVals = this.impares.replace(/;/g, ',').split(',').map(v => parseInt(v.trim(), 10)).filter(v => !isNaN(v));
    const pares = this.useParImpar ? paresVals : [];
    const impares = this.useParImpar ? imparesVals : [];
    const colMinArr = this.colMin.split(',').map(v => parseInt(v.trim(), 10));
    const colMaxArr = this.colMax.split(',').map(v => parseInt(v.trim(), 10));
    const abcdMinArr = this.abcdMin.split(',').map(v => parseInt(v.trim(), 10));
    const abcdMaxArr = this.abcdMax.split(',').map(v => parseInt(v.trim(), 10));
    this.loading = true;
    this.resultsService.getFilterSelection({
      cutoff: cutoffVal,
      aplicarPI: this.useParImpar,
      aplicarCRE: this.aplicarCRE,
      aplicarSalto: this.aplicarSalto,
      aplicarNAH: this.aplicarNAH,
      nahVar: this.nahVar,
      aplicarABCD: this.aplicarABCD,
      aplicarTresConsec: this.aplicarTresConsec,
      colMin: colMinArr,
      colMax: colMaxArr,
      abcdMin: abcdMinArr,
      abcdMax: abcdMaxArr,
      pares,
      impares,
      limit: this.limit
    }).subscribe(res => {
      this.totalBase = res.totalBase;
      this.totalFiltrado = res.totalFiltrado;
      this.nahBase = res.nahBase;
      this.nahAllowed = res.nahAllowed || [];
      this.nahAllowedTooltip = this.nahAllowed.map(n => n.join('/')).join('; ');
      this.items = res.results;
      this.nextConcurso = undefined;
      this.nextDezenas = [];
      this.loading = false;
    }, _ => { this.loading = false; });
  }

  check(): void {
    const cutoffVal = parseInt(this.cutoff, 10);
    if (isNaN(cutoffVal) || this.items.length === 0) return;
    const bets = this.items.map(it => it.dezenas);
    this.loading = true;
    this.resultsService.checkSelection(cutoffVal, bets).subscribe(res => {
      this.nextConcurso = res.nextConcurso;
      this.nextDezenas = res.nextDezenas || [];
      this.nextInfo = res.nextInfo || undefined;
      const acertosMap = new Map<string, number>();
      res.results.forEach(r => acertosMap.set(r.dezenas.join(','), r.acertos));
      this.items = this.items.map(it => ({
        ...it,
        acertos: acertosMap.get(it.dezenas.join(',')) ?? it.acertos
      }));
      this.items.sort((a, b) => (b.acertos ?? 0) - (a.acertos ?? 0));
      this.loading = false;
    }, _ => { this.loading = false; });
  }
}
