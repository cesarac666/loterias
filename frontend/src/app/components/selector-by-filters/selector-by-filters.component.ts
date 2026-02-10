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
  nahList = '';
  nahListApplied: number[][] = [];
  nahListProvided = false;
  nahListInvalid = false;
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
  selectionMode = 'random';
  selectionSeed = '';
  selectionModeApplied = '';
  selectionSeedApplied: number | null = null;
  selectionModeLabels: { [key: string]: string } = {
    random: 'Aleatória',
    diversidade: 'Diversidade (Jaccard)',
    estratificada: 'Estratificada (grupos)',
    distantes: 'Distantes (ID base)',
    primeiras: 'Primeiras (ordem da base)'
  };
  saving = false;
  saveStatus = '';
  saveError = '';

  // Outputs
  totalBase = 0;
  totalFiltrado = 0;
  nahBase: [number, number, number] | null = null;
  nahAllowed: [number, number, number][] = [];
  nahAllowedTooltip = '';
  items: { dezenas: number[]; qtdPares: number; qtdImpares: number; nahN?: number; nahA?: number; nahH?: number; acertos?: number }[] = [];
  nextConcurso?: number;
  nextDezenas: number[] = [];
  nextInfo?: { qtdPares: number; qtdImpares: number; maiorSalto: number; maiorConsecutivas: number; countC: number[]; abcdCounts: number[] } | null;
  filtersCheck?: { [name: string]: boolean } | null;
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
    const seedValRaw = this.selectionSeed.trim();
    const seedVal = seedValRaw ? parseInt(seedValRaw, 10) : undefined;
    const selectionSeed = Number.isNaN(seedVal) ? undefined : seedVal;
    const nahList = this.nahList.trim();
    const aplicarNAHEfetivo = this.aplicarNAH || !!nahList;
    this.loading = true;
    this.resultsService.getFilterSelection({
      cutoff: cutoffVal,
      aplicarPI: this.useParImpar,
      aplicarCRE: this.aplicarCRE,
      aplicarSalto: this.aplicarSalto,
      aplicarNAH: aplicarNAHEfetivo,
      nahVar: this.nahVar,
      aplicarABCD: this.aplicarABCD,
      aplicarTresConsec: this.aplicarTresConsec,
      colMin: colMinArr,
      colMax: colMaxArr,
      abcdMin: abcdMinArr,
      abcdMax: abcdMaxArr,
      pares,
      impares,
      limit: this.limit,
      selectionMode: this.selectionMode,
      selectionSeed,
      nahList: nahList || undefined
    }).subscribe(res => {
      this.totalBase = res.totalBase;
      this.totalFiltrado = res.totalFiltrado;
      this.nahBase = res.nahBase;
      this.nahAllowed = res.nahAllowed || [];
      this.nahAllowedTooltip = this.nahAllowed.map(n => n.join('/')).join('; ');
      this.nahListApplied = res.nahList || [];
      this.nahListProvided = !!res.nahListProvided;
      this.nahListInvalid = this.nahListProvided && this.nahListApplied.length === 0;
      this.items = res.results;
      this.nextConcurso = undefined;
      this.nextDezenas = [];
      this.selectionModeApplied = res.selectionMode || this.selectionMode;
      this.selectionSeedApplied = res.selectionSeed ?? (selectionSeed ?? null);
      this.loading = false;
    }, _ => { this.loading = false; });
  }

  saveBets(): void {
    const cutoffVal = parseInt(this.cutoff, 10);
    if (isNaN(cutoffVal)) {
      this.saveError = 'Informe um cutoff valido antes de salvar.';
      return;
    }
    if (!this.items.length) {
      this.saveError = 'Nao ha apostas para salvar.';
      return;
    }
    if (this.saving) {
      return;
    }
    this.saving = true;
    this.saveStatus = 'Salvando apostas...';
    this.saveError = '';
    const bets = this.items.map(it => it.dezenas);
    this.resultsService.saveLotofacilBets(cutoffVal, bets).subscribe({
      next: (res) => {
        const inserted = res.inserted ?? 0;
        const already = res.alreadySaved ?? 0;
        const invalid = res.invalid ?? 0;
        this.saveStatus = `Salvas: ${inserted}, ja existentes: ${already}` + (invalid ? `, invalidas: ${invalid}` : '');
        this.saving = false;
      },
      error: () => {
        this.saveError = 'Falha ao salvar apostas.';
        this.saveStatus = '';
        this.saving = false;
      }
    });
  }

  check(): void {
    const cutoffVal = parseInt(this.cutoff, 10);
    if (isNaN(cutoffVal) || this.items.length === 0) return;
    const bets = this.items.map(it => it.dezenas);
    this.loading = true;
    const options = {
      aplicarPI: this.useParImpar,
      aplicarCRE: this.aplicarCRE,
      aplicarSalto: this.aplicarSalto,
      aplicarNAH: this.aplicarNAH,
      nahVar: this.nahVar,
      aplicarABCD: this.aplicarABCD,
      aplicarTresConsec: this.aplicarTresConsec,
      aplicarBolaVez: false,
      aplicarLosangoCentro: false,
      aplicarOnzeQuinze: false,
      aplicarMaxUmCinco: false,
      colMin: this.colMin.split(',').map(v => parseInt(v.trim(), 10)),
      colMax: this.colMax.split(',').map(v => parseInt(v.trim(), 10)),
      abcdMin: this.abcdMin.split(',').map(v => parseInt(v.trim(), 10)),
      abcdMax: this.abcdMax.split(',').map(v => parseInt(v.trim(), 10)),
      pares: this.useParImpar ? this.pares.split(',').map(v => parseInt(v.trim(), 10)).filter(v => !isNaN(v)) : [],
      impares: this.useParImpar ? this.impares.split(',').map(v => parseInt(v.trim(), 10)).filter(v => !isNaN(v)) : [],
    };
    this.resultsService.checkSelection(cutoffVal, bets, options).subscribe(res => {
      this.nextConcurso = res.nextConcurso;
      this.nextDezenas = res.nextDezenas || [];
      this.nextInfo = res.nextInfo || undefined;
      this.filtersCheck = res.filtersCheck || undefined;
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
