import { Component, OnInit } from '@angular/core';
import {
  DiaDaSorteService,
  DiaDaSorteBet,
  DiaDaSorteBetsResponse,
  DiaDaSorteLastResult,
  DiaDaSorteSaveResponse,
  DiaDaSorteSummary
} from '../../services/dia-da-sorte.service';

type RangeField = { min: string; max: string };

interface RangeDefaults {
  readonly min: string;
  readonly max: string;
}

@Component({
  selector: 'app-dia-da-sorte-bets',
  templateUrl: './dia-da-sorte-bets.component.html',
  styleUrls: ['./dia-da-sorte-bets.component.css']
})
export class DiaDaSorteBetsComponent implements OnInit {
  results: DiaDaSorteBet[] = [];
  total = 0;
  limit = 100;
  offset = 0;
  loading = false;
  error?: string;
  latestResult?: DiaDaSorteLastResult;
  summaryDefaults: DiaDaSorteSummary | null = null;
  saving = false;
  saveStatus?: string;
  saveError?: string;

  paresMin = '2';
  paresMax = '5';
  imparesMin = '2';
  imparesMax = '5';
  maxConsecMin = '1';
  maxConsecMax = '5';
  maiorSaltoMin = '5';
  maiorSaltoMax = '16';
  isolatedMin = '0';
  isolatedMax = '4';
  nahNMin = '4';
  nahNMax = '7';
  nahAMin = '0';
  nahAMax = '3';
  nahHMin = '0';
  nahHMax = '1';

  private readonly defaultQdls: RangeDefaults[] = [
    { min: '0', max: '3' },
    { min: '0', max: '5' },
    { min: '0', max: '4' },
    { min: '0', max: '3' },
    { min: '0', max: '1' }
  ];

  private readonly defaultUnits: RangeDefaults[] = [
    { min: '0', max: '2' },
    { min: '0', max: '3' },
    { min: '0', max: '2' },
    { min: '0', max: '3' },
    { min: '0', max: '2' },
    { min: '0', max: '2' },
    { min: '0', max: '2' },
    { min: '0', max: '2' },
    { min: '0', max: '2' },
    { min: '0', max: '2' }
  ];

  private readonly defaultTens: RangeDefaults[] = [
    { min: '0', max: '4' },
    { min: '0', max: '5' },
    { min: '0', max: '5' },
    { min: '0', max: '1' }
  ];

  readonly unitDigits = Array.from({ length: 10 }, (_, i) => String(i));
  readonly tenDigits = Array.from({ length: 4 }, (_, i) => String(i));
  qdlsFilters: RangeField[] = [];
  unitFilters: RangeField[] = [];
  tenFilters: RangeField[] = [];

  constructor(private readonly diaDaSorteService: DiaDaSorteService) {
    this.resetRangeFilters();
  }

  ngOnInit(): void {
    this.loadLatestResult();
    this.loadSummaryDefaults();
  }

  applyFilters(): void {
    this.loading = true;
    this.saving = false;
    this.error = undefined;
    this.saveStatus = undefined;
    this.saveError = undefined;
    const payload = this.buildPayload();
    this.diaDaSorteService.filterBets(payload).subscribe({
      next: (response: DiaDaSorteBetsResponse) => {
        this.results = response.results;
        this.total = response.total;
        this.limit = response.limit;
        this.offset = response.offset;
        this.loading = false;
      },
      error: (err) => {
        console.error('Falha ao filtrar apostas', err);
        this.results = [];
        this.loading = false;
        this.error = 'Falha ao carregar apostas filtradas.';
      }
    });
  }

  loadLatestResult(): void {
    this.diaDaSorteService.getLastResult().subscribe({
      next: (result: DiaDaSorteLastResult) => {
        this.latestResult = result;
      },
      error: (err) => {
        console.error('Falha ao obter ultimo resultado do Dia da Sorte', err);
        this.latestResult = undefined;
      }
    });
  }

  loadSummaryDefaults(): void {
    this.diaDaSorteService.getResultsSummary().subscribe({
      next: (summary: DiaDaSorteSummary) => {
        this.summaryDefaults = summary;
        this.restoreDefaultFilters(false);
        this.applyFilters();
      },
      error: (err) => {
        console.error('Falha ao carregar resumo estatistico do Dia da Sorte', err);
        this.summaryDefaults = null;
        this.restoreDefaultFilters(false);
        this.applyFilters();
      }
    });
  }

  restoreDefaultFilters(apply: boolean = false): void {
    const summary = this.summaryDefaults;
    const toString = (value: number | null | undefined, fallback: string): string =>
      value != null ? String(value) : fallback;

    if (summary) {
      this.paresMin = toString(summary.pares?.min, '2');
      this.paresMax = toString(summary.pares?.max, '5');
      this.imparesMin = toString(summary.impares?.min, '2');
      this.imparesMax = toString(summary.impares?.max, '5');
      this.maxConsecMin = toString(summary.maxConsec?.min, '1');
      this.maxConsecMax = toString(summary.maxConsec?.max, '5');
      this.maiorSaltoMin = toString(summary.maiorSalto?.min, '5');
      this.maiorSaltoMax = toString(summary.maiorSalto?.max, '16');
      this.isolatedMin = toString(summary.isolatedCount?.min, '0');
      this.isolatedMax = toString(summary.isolatedCount?.max, '4');
      this.nahNMin = toString(summary.nah.n?.min ?? null, '4');
      this.nahNMax = toString(summary.nah.n?.max ?? null, '7');
      this.nahAMin = toString(summary.nah.a?.min ?? null, '0');
      this.nahAMax = toString(summary.nah.a?.max ?? null, '3');
      this.nahHMin = toString(summary.nah.h?.min ?? null, '0');
      this.nahHMax = toString(summary.nah.h?.max ?? null, '1');

      const qdlsSummary = summary.qdls ?? [];
      this.qdlsFilters = this.defaultQdls.map((defaults, idx) => ({
        min: toString(qdlsSummary[idx]?.min, defaults.min),
        max: toString(qdlsSummary[idx]?.max, defaults.max)
      }));

      const unitSummary = summary.digitStats.units;
      this.unitFilters = this.unitDigits.map((digit, idx) => ({
        min: toString(unitSummary[digit]?.min, this.defaultUnits[idx].min),
        max: toString(unitSummary[digit]?.max, this.defaultUnits[idx].max)
      }));

      const tenSummary = summary.digitStats.tens;
      this.tenFilters = this.tenDigits.map((digit, idx) => ({
        min: toString(tenSummary[digit]?.min, this.defaultTens[idx].min),
        max: toString(tenSummary[digit]?.max, this.defaultTens[idx].max)
      }));
    } else {
      this.paresMin = '2';
      this.paresMax = '5';
      this.imparesMin = '2';
      this.imparesMax = '5';
      this.maxConsecMin = '1';
      this.maxConsecMax = '5';
      this.maiorSaltoMin = '5';
      this.maiorSaltoMax = '16';
      this.isolatedMin = '0';
      this.isolatedMax = '4';
      this.nahNMin = '4';
      this.nahNMax = '7';
      this.nahAMin = '0';
      this.nahAMax = '3';
      this.nahHMin = '0';
      this.nahHMax = '1';
      this.resetRangeFilters();
    }

    this.limit = 100;
    this.offset = 0;
    this.saveStatus = undefined;
    this.saveError = undefined;
    if (apply) {
      this.applyFilters();
    }
  }

  saveFilteredBets(): void {
    if (this.loading || this.saving || this.total === 0) {
      return;
    }
    this.saving = true;
    this.saveStatus = undefined;
    this.saveError = undefined;
    const payload = this.buildPayload();
    this.diaDaSorteService.saveFilteredBets(payload).subscribe({
      next: (response: DiaDaSorteSaveResponse) => {
        if (!response.totalMatches) {
          this.saveStatus = response.message ?? 'Nenhuma aposta encontrada para salvar.';
        } else {
          const inseridas = response.inserted;
          const jaExistiam = response.alreadySaved;
          this.saveStatus = `Concurso ${response.nextConcurso}: ${inseridas} aposta(s) salva(s), ${jaExistiam} ja existiam.`;
        }
      },
      error: (err) => {
        console.error('Falha ao salvar apostas filtradas', err);
        this.saveError = 'Falha ao salvar apostas filtradas.';
        this.saving = false;
      },
      complete: () => {
        this.saving = false;
      }
    });
  }

  formatDigitStats(bet: DiaDaSorteBet): string {
    const stats = bet.digitStats;
    const formatMap = (prefix: string, values: Record<string, number>): string => {
      const partes = Object.entries(values)
        .filter(([, quantidade]) => quantidade > 0)
        .map(([digito, quantidade]) => `${prefix}${digito}=${quantidade}`);
      return partes.length ? partes.join(', ') : `${prefix}-`;
    };
    return `${formatMap('U', stats.units)} | ${formatMap('D', stats.tens)}`;
  }

  formatQdls(bet: DiaDaSorteBet): string {
    return bet.qdls.map((valor, indice) => `S${indice + 1}=${valor}`).join(', ');
  }

  formatNah(bet: DiaDaSorteBet): string {
    const { nahN, nahA, nahH } = bet;
    if (nahN == null || nahA == null || nahH == null) {
      return 'N/A';
    }
    return `${nahN}-${nahA}-${nahH}`;
  }

  private resetRangeFilters(): void {
    this.qdlsFilters = this.defaultQdls.map(({ min, max }) => ({ min, max }));
    this.unitFilters = this.defaultUnits.map(({ min, max }) => ({ min, max }));
    this.tenFilters = this.defaultTens.map(({ min, max }) => ({ min, max }));
  }

  private buildPayload(): any {
    const parseNumber = (value: string): number | null => {
      if (value === null || value === undefined) {
        return null;
      }
      const trimmed = value.toString().trim();
      if (!trimmed) {
        return null;
      }
      const num = Number(trimmed);
      return Number.isFinite(num) ? num : null;
    };

    const payload: any = {
      limit: this.limit,
      offset: this.offset
    };

    const setRange = (minValue: string, maxValue: string, minKey: string, maxKey: string) => {
      const minParsed = parseNumber(minValue);
      const maxParsed = parseNumber(maxValue);
      if (minParsed !== null) {
        payload[minKey] = minParsed;
      }
      if (maxParsed !== null) {
        payload[maxKey] = maxParsed;
      }
    };

    setRange(this.paresMin, this.paresMax, 'paresMin', 'paresMax');
    setRange(this.imparesMin, this.imparesMax, 'imparesMin', 'imparesMax');
    setRange(this.maxConsecMin, this.maxConsecMax, 'maxConsecMin', 'maxConsecMax');
    setRange(this.maiorSaltoMin, this.maiorSaltoMax, 'maiorSaltoMin', 'maiorSaltoMax');
    setRange(this.isolatedMin, this.isolatedMax, 'isolatedMin', 'isolatedMax');
    setRange(this.nahNMin, this.nahNMax, 'nahNMin', 'nahNMax');
    setRange(this.nahAMin, this.nahAMax, 'nahAMin', 'nahAMax');
    setRange(this.nahHMin, this.nahHMax, 'nahHMin', 'nahHMax');

    const buildRangeArray = (filters: RangeField[]): (number | null)[] | undefined => {
      const arr = filters.map((f) => parseNumber(f.min));
      return arr.some((value) => value !== null) ? arr : undefined;
    };

    const buildRangeArrayMax = (filters: RangeField[]): (number | null)[] | undefined => {
      const arr = filters.map((f) => parseNumber(f.max));
      return arr.some((value) => value !== null) ? arr : undefined;
    };

    const qdlsMin = buildRangeArray(this.qdlsFilters);
    const qdlsMax = buildRangeArrayMax(this.qdlsFilters);
    if (qdlsMin) {
      payload.qdlsMin = qdlsMin;
    }
    if (qdlsMax) {
      payload.qdlsMax = qdlsMax;
    }

    const unitsMin = buildRangeArray(this.unitFilters);
    const unitsMax = buildRangeArrayMax(this.unitFilters);
    if (unitsMin) {
      payload.unitsMin = unitsMin;
    }
    if (unitsMax) {
      payload.unitsMax = unitsMax;
    }

    const tensMin = buildRangeArray(this.tenFilters);
    const tensMax = buildRangeArrayMax(this.tenFilters);
    if (tensMin) {
      payload.tensMin = tensMin;
    }
    if (tensMax) {
      payload.tensMax = tensMax;
    }

    return payload;
  }
}
