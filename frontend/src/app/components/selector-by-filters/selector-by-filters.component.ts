import { Component, OnDestroy } from '@angular/core';
import {
  FilterBacktestDetail,
  FilterBacktestModeSummary,
  LotofacilBolaDaVezFrequenciaRow,
  ResultsService
} from '../../results.service';

@Component({
  selector: 'app-selector-by-filters',
  templateUrl: './selector-by-filters2.component.html',
  styleUrls: ['./selector-by-filters.component.css']
})
export class SelectorByFiltersComponent implements OnDestroy {
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
  aplicarBolaVez = true;
  aplicarLosangoCentro = true;
  aplicarOnzeQuinze = true;
  aplicarCountCMinUmQuatro = true;
  aplicarMaxUmCinco = true;
  aplicarCountCS = true;
  aplicarCantos = true;
  aplicarDiagonais = true;
  aplicarSoma = true;
  somaMin = '185';
  somaMax = '205';
  bolaVezEntram = '';
  bolaVezSaem = '';
  colMin = '2,1,1,1,1';
  colMax = '5,5,4,5,5';
  abcdMin = '0,2,4,0';
  abcdMax = '3,8,10,5';
  useParImpar = true;
  pares = '6,7,8';
  impares = '7,8,9';
  padraoLinha = '';
  padraoLinhaLinha2 = '';
  padraoLinhaLinha5 = '';
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
    primeiras: 'Primeiras (ordem da base)',
    historica: 'Historica (freq + transicao + soma)'
  };
  saving = false;
  saveStatus = '';
  saveError = '';
  bolaVezCalcLoading = false;
  bolaVezCalcError = '';
  bolaVezCalcCutoff: number | null = null;
  bolaVezCalcCutoffSolicitado: number | null = null;
  bolaVezCalcTotalHistorico = 0;
  bolaVezCalcDataCutoff = '';
  bolaVezCalcResultadoCutoff: number[] = [];
  bolaVezCalcEntram: number[] = [];
  bolaVezCalcSaem: number[] = [];
  bolaVezCalcFrequencia: LotofacilBolaDaVezFrequenciaRow[] = [];
  showBolaVezFrequenciaModal = false;
  backtestWindow = 60;
  backtestTopN = 100;
  backtestStep = 1;
  backtestLoading = false;
  backtestElapsedSeconds = 0;
  backtestError = '';
  backtestFromCutoff: number | null = null;
  backtestToCutoff: number | null = null;
  backtestTotalAvaliados = 0;
  backtestWinnerInFilteredCount = 0;
  backtestWinnerInFilteredRate = 0;
  backtestModeSummaries: FilterBacktestModeSummary[] = [];
  backtestDetails: FilterBacktestDetail[] = [];
  showBacktestAuditModal = false;
  private backtestTimerId: any = null;

  // Outputs
  totalBase = 0;
  totalFiltrado = 0;
  nahBase: [number, number, number] | null = null;
  nahAllowed: [number, number, number][] = [];
  nahAllowedTooltip = '';
  items: { id?: number; dezenas: number[]; qtdPares: number; qtdImpares: number; nahN?: number; nahA?: number; nahH?: number; acertos?: number }[] = [];
  nextConcurso?: number;
  nextDezenas: number[] = [];
  nextInfo?: { qtdPares: number; qtdImpares: number; maiorSalto: number; maiorConsecutivas: number; countC: number[]; abcdCounts: number[] } | null;
  filtersCheck?: { [name: string]: boolean } | null;
  loading = false;

  constructor(private resultsService: ResultsService) {}

  private parseCsvNumbers(value: string): number[] {
    return value
      .replace(/;/g, ',')
      .split(',')
      .map(v => parseInt(v.trim(), 10))
      .filter(v => !isNaN(v));
  }

  private parseOptionalInt(value: string | number | null | undefined): number | undefined {
    if (value == null || value === '') {
      return undefined;
    }
    if (typeof value === 'number') {
      return Number.isFinite(value) ? Math.trunc(value) : undefined;
    }
    const parsed = parseInt(value.trim(), 10);
    return Number.isNaN(parsed) ? undefined : parsed;
  }

  onPadraoLinhaChange(): void {
    if (this.padraoLinha !== 'quase 3 por linha') {
      this.padraoLinhaLinha2 = '';
    }
    if (this.padraoLinha !== '1 linha completa') {
      this.padraoLinhaLinha5 = '';
    }
  }

  run(): void {
    const cutoffVal = parseInt(this.cutoff, 10);
    if (isNaN(cutoffVal)) return;
    const paresVals = this.parseCsvNumbers(this.pares);
    const imparesVals = this.parseCsvNumbers(this.impares);
    const pares = this.useParImpar ? paresVals : [];
    const impares = this.useParImpar ? imparesVals : [];
    const colMinArr = this.colMin.split(',').map(v => parseInt(v.trim(), 10));
    const colMaxArr = this.colMax.split(',').map(v => parseInt(v.trim(), 10));
    const abcdMinArr = this.abcdMin.split(',').map(v => parseInt(v.trim(), 10));
    const abcdMaxArr = this.abcdMax.split(',').map(v => parseInt(v.trim(), 10));
    const somaMin = this.parseOptionalInt(this.somaMin);
    const somaMax = this.parseOptionalInt(this.somaMax);
    const bolaVezEntram = this.parseCsvNumbers(this.bolaVezEntram);
    const bolaVezSaem = this.parseCsvNumbers(this.bolaVezSaem);
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
      aplicarBolaVez: this.aplicarBolaVez,
      aplicarLosangoCentro: this.aplicarLosangoCentro,
      aplicarOnzeQuinze: this.aplicarOnzeQuinze,
      aplicarCountCMinUmQuatro: this.aplicarCountCMinUmQuatro,
      aplicarMaxUmCinco: this.aplicarMaxUmCinco,
      aplicarCountCS: this.aplicarCountCS,
      aplicarCantos: this.aplicarCantos,
      aplicarDiagonais: this.aplicarDiagonais,
      aplicarSoma: this.aplicarSoma,
      somaMin,
      somaMax,
      bolaVezEntram: bolaVezEntram.length ? bolaVezEntram : undefined,
      bolaVezSaem: bolaVezSaem.length ? bolaVezSaem : undefined,
      colMin: colMinArr,
      colMax: colMaxArr,
      abcdMin: abcdMinArr,
      abcdMax: abcdMaxArr,
      pares,
      impares,
      limit: this.limit,
      selectionMode: this.selectionMode,
      selectionSeed,
      padraoLinha: this.padraoLinha || undefined,
      padraoLinhaLinha2: this.parseOptionalInt(this.padraoLinhaLinha2),
      padraoLinhaLinha5: this.parseOptionalInt(this.padraoLinhaLinha5),
      nahList: nahList || undefined
    }).subscribe(res => {
      this.totalBase = res.totalBase;
      this.totalFiltrado = res.totalFiltrado;
      this.padraoLinha = res.padraoLinha || this.padraoLinha;
      this.padraoLinhaLinha2 = res.padraoLinhaLinha2 != null ? String(res.padraoLinhaLinha2) : this.padraoLinhaLinha2;
      this.padraoLinhaLinha5 = res.padraoLinhaLinha5 != null ? String(res.padraoLinhaLinha5) : this.padraoLinhaLinha5;
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
    const nahList = this.nahList.trim();
    const aplicarNAHEfetivo = this.aplicarNAH || !!nahList;
    this.loading = true;
    const options = {
      aplicarPI: this.useParImpar,
      aplicarCRE: this.aplicarCRE,
      aplicarSalto: this.aplicarSalto,
      aplicarNAH: aplicarNAHEfetivo,
      nahVar: this.nahVar,
      aplicarABCD: this.aplicarABCD,
      aplicarTresConsec: this.aplicarTresConsec,
      aplicarBolaVez: this.aplicarBolaVez,
      aplicarLosangoCentro: this.aplicarLosangoCentro,
      aplicarOnzeQuinze: this.aplicarOnzeQuinze,
      aplicarCountCMinUmQuatro: this.aplicarCountCMinUmQuatro,
      aplicarMaxUmCinco: this.aplicarMaxUmCinco,
      aplicarCountCS: this.aplicarCountCS,
      aplicarCantos: this.aplicarCantos,
      aplicarDiagonais: this.aplicarDiagonais,
      aplicarSoma: this.aplicarSoma,
      somaMin: this.parseOptionalInt(this.somaMin),
      somaMax: this.parseOptionalInt(this.somaMax),
      bolaVezEntram: this.parseCsvNumbers(this.bolaVezEntram),
      bolaVezSaem: this.parseCsvNumbers(this.bolaVezSaem),
      colMin: this.colMin.split(',').map(v => parseInt(v.trim(), 10)),
      colMax: this.colMax.split(',').map(v => parseInt(v.trim(), 10)),
      abcdMin: this.abcdMin.split(',').map(v => parseInt(v.trim(), 10)),
      abcdMax: this.abcdMax.split(',').map(v => parseInt(v.trim(), 10)),
      pares: this.useParImpar ? this.parseCsvNumbers(this.pares) : [],
      impares: this.useParImpar ? this.parseCsvNumbers(this.impares) : [],
      padraoLinha: this.padraoLinha || undefined,
      padraoLinhaLinha2: this.parseOptionalInt(this.padraoLinhaLinha2),
      padraoLinhaLinha5: this.parseOptionalInt(this.padraoLinhaLinha5),
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

  calculateBolaDaVez(): void {
    const cutoffVal = parseInt(this.cutoff, 10);
    if (isNaN(cutoffVal)) {
      this.bolaVezCalcError = 'Informe um cutoff valido para calcular bola da vez.';
      this.bolaVezCalcEntram = [];
      this.bolaVezCalcSaem = [];
      this.bolaVezCalcCutoff = null;
      this.bolaVezCalcCutoffSolicitado = null;
      this.bolaVezCalcTotalHistorico = 0;
      this.bolaVezCalcDataCutoff = '';
      this.bolaVezCalcResultadoCutoff = [];
      this.bolaVezCalcFrequencia = [];
      this.showBolaVezFrequenciaModal = false;
      return;
    }

    this.bolaVezCalcLoading = true;
    this.bolaVezCalcError = '';
    this.resultsService.getLotofacilBolaDaVez(cutoffVal).subscribe({
      next: (res) => {
        this.bolaVezCalcCutoff = res.cutoff;
        this.bolaVezCalcCutoffSolicitado = res.cutoffSolicitado ?? cutoffVal;
        this.bolaVezCalcTotalHistorico = res.totalHistorico || 0;
        this.bolaVezCalcDataCutoff = res.dataCutoff || '';
        this.bolaVezCalcResultadoCutoff = res.resultadoCutoff || [];
        this.bolaVezCalcEntram = res.entram || [];
        this.bolaVezCalcSaem = res.saem || [];
        this.bolaVezCalcFrequencia = res.frequencia || [];
        this.bolaVezCalcLoading = false;
      },
      error: () => {
        this.bolaVezCalcError = 'Falha ao calcular bola da vez.';
        this.bolaVezCalcCutoff = null;
        this.bolaVezCalcCutoffSolicitado = null;
        this.bolaVezCalcTotalHistorico = 0;
        this.bolaVezCalcDataCutoff = '';
        this.bolaVezCalcResultadoCutoff = [];
        this.bolaVezCalcEntram = [];
        this.bolaVezCalcSaem = [];
        this.bolaVezCalcFrequencia = [];
        this.showBolaVezFrequenciaModal = false;
        this.bolaVezCalcLoading = false;
      }
    });
  }

  useCalculatedBolaDaVez(): void {
    if (!this.bolaVezCalcEntram.length && !this.bolaVezCalcSaem.length) {
      return;
    }
    this.bolaVezEntram = this.bolaVezCalcEntram.join(',');
    this.bolaVezSaem = this.bolaVezCalcSaem.join(',');
  }

  openBolaVezFrequenciaModal(): void {
    if (!this.bolaVezCalcFrequencia.length) {
      return;
    }
    this.showBolaVezFrequenciaModal = true;
  }

  closeBolaVezFrequenciaModal(): void {
    this.showBolaVezFrequenciaModal = false;
  }

  openBacktestAuditModal(): void {
    if (!this.backtestDetails.length) {
      return;
    }
    this.showBacktestAuditModal = true;
  }

  closeBacktestAuditModal(): void {
    this.showBacktestAuditModal = false;
  }

  ngOnDestroy(): void {
    this.stopBacktestTimer();
  }

  modePos(modeHits: { [mode: string]: number | null } | undefined, mode: string): number | null {
    if (!modeHits || !(mode in modeHits)) {
      return null;
    }
    return modeHits[mode];
  }

  private startBacktestTimer(): void {
    this.stopBacktestTimer();
    this.backtestElapsedSeconds = 0;
    this.backtestTimerId = setInterval(() => {
      this.backtestElapsedSeconds += 1;
    }, 1000);
  }

  private stopBacktestTimer(): void {
    if (this.backtestTimerId) {
      clearInterval(this.backtestTimerId);
      this.backtestTimerId = null;
    }
  }

  runBacktest(): void {
    const cutoffVal = parseInt(this.cutoff, 10);
    if (isNaN(cutoffVal)) {
      this.backtestError = 'Informe um cutoff valido para o backtest.';
      return;
    }

    const colMinArr = this.colMin.split(',').map(v => parseInt(v.trim(), 10));
    const colMaxArr = this.colMax.split(',').map(v => parseInt(v.trim(), 10));
    const abcdMinArr = this.abcdMin.split(',').map(v => parseInt(v.trim(), 10));
    const abcdMaxArr = this.abcdMax.split(',').map(v => parseInt(v.trim(), 10));
    const somaMin = this.parseOptionalInt(this.somaMin);
    const somaMax = this.parseOptionalInt(this.somaMax);
    const paresVals = this.parseCsvNumbers(this.pares);
    const imparesVals = this.parseCsvNumbers(this.impares);
    const bolaVezEntram = this.parseCsvNumbers(this.bolaVezEntram);
    const bolaVezSaem = this.parseCsvNumbers(this.bolaVezSaem);
    const nahList = this.nahList.trim();
    const aplicarNAHEfetivo = this.aplicarNAH || !!nahList;

    this.backtestLoading = true;
    this.backtestError = '';
    this.startBacktestTimer();
    this.resultsService.getFilterBacktest({
      cutoff: cutoffVal,
      aplicarPI: this.useParImpar,
      aplicarCRE: this.aplicarCRE,
      aplicarSalto: this.aplicarSalto,
      aplicarNAH: aplicarNAHEfetivo,
      nahVar: this.nahVar,
      aplicarABCD: this.aplicarABCD,
      aplicarTresConsec: this.aplicarTresConsec,
      aplicarBolaVez: this.aplicarBolaVez,
      aplicarLosangoCentro: this.aplicarLosangoCentro,
      aplicarOnzeQuinze: this.aplicarOnzeQuinze,
      aplicarCountCMinUmQuatro: this.aplicarCountCMinUmQuatro,
      aplicarMaxUmCinco: this.aplicarMaxUmCinco,
      aplicarCountCS: this.aplicarCountCS,
      aplicarCantos: this.aplicarCantos,
      aplicarDiagonais: this.aplicarDiagonais,
      aplicarSoma: this.aplicarSoma,
      somaMin,
      somaMax,
      bolaVezEntram: bolaVezEntram.length ? bolaVezEntram : undefined,
      bolaVezSaem: bolaVezSaem.length ? bolaVezSaem : undefined,
      colMin: colMinArr,
      colMax: colMaxArr,
      abcdMin: abcdMinArr,
      abcdMax: abcdMaxArr,
      pares: this.useParImpar ? paresVals : [],
      impares: this.useParImpar ? imparesVals : [],
      padraoLinha: this.padraoLinha || undefined,
      padraoLinhaLinha2: this.parseOptionalInt(this.padraoLinhaLinha2),
      padraoLinhaLinha5: this.parseOptionalInt(this.padraoLinhaLinha5),
      nahList: nahList || undefined,
      backtestWindow: this.backtestWindow,
      backtestTopN: this.backtestTopN,
      backtestStep: this.backtestStep
    }).subscribe({
      next: (res) => {
        this.backtestFromCutoff = res.fromCutoff ?? null;
        this.backtestToCutoff = res.toCutoff ?? null;
        this.backtestTotalAvaliados = res.totalAvaliados || 0;
        this.backtestWinnerInFilteredCount = res.winnerInFilteredCount || 0;
        this.backtestWinnerInFilteredRate = res.winnerInFilteredRate || 0;
        this.padraoLinha = res.padraoLinha || this.padraoLinha;
        this.padraoLinhaLinha2 = res.padraoLinhaLinha2 != null ? String(res.padraoLinhaLinha2) : this.padraoLinhaLinha2;
        this.padraoLinhaLinha5 = res.padraoLinhaLinha5 != null ? String(res.padraoLinhaLinha5) : this.padraoLinhaLinha5;
        this.backtestModeSummaries = res.modes || [];
        this.backtestDetails = res.details || [];
        this.showBacktestAuditModal = false;
        this.backtestLoading = false;
        this.stopBacktestTimer();
      },
      error: (err) => {
        const backendError = err?.error?.error;
        this.backtestError = backendError || 'Falha ao executar backtest.';
        this.showBacktestAuditModal = false;
        this.backtestLoading = false;
        this.stopBacktestTimer();
      }
    });
  }
}
