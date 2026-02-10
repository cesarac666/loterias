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

interface StoredFilters {
  paresMin: string;
  paresMax: string;
  imparesMin: string;
  imparesMax: string;
  maxConsecMin: string;
  maxConsecMax: string;
  maiorSaltoMin: string;
  maiorSaltoMax: string;
  isolatedMin: string;
  isolatedMax: string;
  nahNMin: string;
  nahNMax: string;
  nahAMin: string;
  nahAMax: string;
  nahHMin: string;
  nahHMax: string;
  casalUnidadeMin: string;
  casalUnidadeMax: string;
  qdlsFilters: RangeField[];
  unitFilters: RangeField[];
  tenFilters: RangeField[];
  limit: number;
  offset: number;
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

  private readonly storageKey = 'dia-da-sorte-bets-filters-v1';
  private storedDefaults: StoredFilters | null = null;

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
  casalUnidadeMin = '0';
  casalUnidadeMax = '3';

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
    const restored = this.restoreStoredDefaults();
    this.loadSummaryDefaults();
    if (restored) {
      this.applyFilters(false);
    }
  }

  applyFilters(persist: boolean = true): void {
    this.loading = true;
    this.saving = false;
    this.error = undefined;
    this.saveStatus = undefined;
    this.saveError = undefined;
    const payload = this.buildPayload();
    if (persist) {
      this.persistFilters();
    }
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
        if (!this.storedDefaults) {
          this.restoreDefaultFilters(false);
          this.applyFilters(false);
        }
      },
      error: (err) => {
        console.error('Falha ao carregar resumo estatistico do Dia da Sorte', err);
        this.summaryDefaults = null;
        if (!this.storedDefaults) {
          this.restoreDefaultFilters(false);
          this.applyFilters(false);
        }
      }
    });
  }

  restoreDefaultFilters(apply: boolean = false): void {
    if (this.storedDefaults) {
      this.applyStoredDefaults(this.storedDefaults);
    } else {
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
      this.casalUnidadeMin = '0';
      this.casalUnidadeMax = '3';

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
      this.casalUnidadeMin = '0';
      this.casalUnidadeMax = '3';
      this.resetRangeFilters();
    }

      this.limit = 100;
      this.offset = 0;
    }

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

  private applyStoredDefaults(stored: StoredFilters): void {
    this.paresMin = stored.paresMin;
    this.paresMax = stored.paresMax;
    this.imparesMin = stored.imparesMin;
    this.imparesMax = stored.imparesMax;
    this.maxConsecMin = stored.maxConsecMin;
    this.maxConsecMax = stored.maxConsecMax;
    this.maiorSaltoMin = stored.maiorSaltoMin;
    this.maiorSaltoMax = stored.maiorSaltoMax;
    this.isolatedMin = stored.isolatedMin;
    this.isolatedMax = stored.isolatedMax;
    this.nahNMin = stored.nahNMin;
    this.nahNMax = stored.nahNMax;
    this.nahAMin = stored.nahAMin;
    this.nahAMax = stored.nahAMax;
    this.nahHMin = stored.nahHMin;
    this.nahHMax = stored.nahHMax;
    this.casalUnidadeMin = stored.casalUnidadeMin;
    this.casalUnidadeMax = stored.casalUnidadeMax;
    this.qdlsFilters = stored.qdlsFilters.map((item) => ({ min: item.min, max: item.max }));
    this.unitFilters = stored.unitFilters.map((item) => ({ min: item.min, max: item.max }));
    this.tenFilters = stored.tenFilters.map((item) => ({ min: item.min, max: item.max }));
    this.limit = stored.limit;
    this.offset = stored.offset;
  }

  private restoreStoredDefaults(): boolean {
    const stored = this.readStoredDefaults();
    if (!stored) {
      return false;
    }
    this.storedDefaults = stored;
    this.applyStoredDefaults(stored);
    return true;
  }

  private persistFilters(): void {
    const toStoredString = (value: unknown): string => {
      if (value === null || value === undefined) {
        return '';
      }
      return String(value);
    };
    const stored: StoredFilters = {
      paresMin: toStoredString(this.paresMin),
      paresMax: toStoredString(this.paresMax),
      imparesMin: toStoredString(this.imparesMin),
      imparesMax: toStoredString(this.imparesMax),
      maxConsecMin: toStoredString(this.maxConsecMin),
      maxConsecMax: toStoredString(this.maxConsecMax),
      maiorSaltoMin: toStoredString(this.maiorSaltoMin),
      maiorSaltoMax: toStoredString(this.maiorSaltoMax),
      isolatedMin: toStoredString(this.isolatedMin),
      isolatedMax: toStoredString(this.isolatedMax),
      nahNMin: toStoredString(this.nahNMin),
      nahNMax: toStoredString(this.nahNMax),
      nahAMin: toStoredString(this.nahAMin),
      nahAMax: toStoredString(this.nahAMax),
      nahHMin: toStoredString(this.nahHMin),
      nahHMax: toStoredString(this.nahHMax),
      casalUnidadeMin: toStoredString(this.casalUnidadeMin),
      casalUnidadeMax: toStoredString(this.casalUnidadeMax),
      qdlsFilters: this.qdlsFilters.map((item) => ({
        min: toStoredString(item.min),
        max: toStoredString(item.max)
      })),
      unitFilters: this.unitFilters.map((item) => ({
        min: toStoredString(item.min),
        max: toStoredString(item.max)
      })),
      tenFilters: this.tenFilters.map((item) => ({
        min: toStoredString(item.min),
        max: toStoredString(item.max)
      })),
      limit: this.limit,
      offset: this.offset
    };
    this.storedDefaults = stored;
    const storage = this.getStorage();
    if (!storage) {
      return;
    }
    try {
      storage.setItem(this.storageKey, JSON.stringify(stored));
    } catch (err) {
      console.warn('Falha ao salvar filtros no armazenamento local.', err);
    }
  }

  private readStoredDefaults(): StoredFilters | null {
    const storage = this.getStorage();
    if (!storage) {
      return null;
    }
    const raw = storage.getItem(this.storageKey);
    if (!raw) {
      return null;
    }
    try {
      const parsed = JSON.parse(raw) as Partial<StoredFilters>;
      if (!parsed || typeof parsed !== 'object') {
        return null;
      }
      const coerceString = (value: unknown, fallback: string): string => {
        if (typeof value === 'string' || typeof value === 'number') {
          return String(value);
        }
        return fallback;
      };
      const coerceRangeField = (value: unknown, fallback: RangeField): RangeField => {
        if (value && typeof value === 'object') {
          const maybeValue = value as { min?: unknown; max?: unknown };
          return {
            min: coerceString(maybeValue.min, fallback.min),
            max: coerceString(maybeValue.max, fallback.max)
          };
        }
        return { min: fallback.min, max: fallback.max };
      };
      const coerceRangeArray = (value: unknown, defaults: RangeDefaults[]): RangeField[] => {
        const source = Array.isArray(value) ? value : [];
        return defaults.map((defaultsForIndex, index) =>
          coerceRangeField(source[index], { min: defaultsForIndex.min, max: defaultsForIndex.max })
        );
      };

      const limit = typeof parsed.limit === 'number' && Number.isFinite(parsed.limit) ? parsed.limit : 100;
      const offset = typeof parsed.offset === 'number' && Number.isFinite(parsed.offset) ? parsed.offset : 0;

      return {
        paresMin: coerceString(parsed.paresMin, this.paresMin),
        paresMax: coerceString(parsed.paresMax, this.paresMax),
        imparesMin: coerceString(parsed.imparesMin, this.imparesMin),
        imparesMax: coerceString(parsed.imparesMax, this.imparesMax),
        maxConsecMin: coerceString(parsed.maxConsecMin, this.maxConsecMin),
        maxConsecMax: coerceString(parsed.maxConsecMax, this.maxConsecMax),
        maiorSaltoMin: coerceString(parsed.maiorSaltoMin, this.maiorSaltoMin),
        maiorSaltoMax: coerceString(parsed.maiorSaltoMax, this.maiorSaltoMax),
        isolatedMin: coerceString(parsed.isolatedMin, this.isolatedMin),
        isolatedMax: coerceString(parsed.isolatedMax, this.isolatedMax),
        nahNMin: coerceString(parsed.nahNMin, this.nahNMin),
        nahNMax: coerceString(parsed.nahNMax, this.nahNMax),
        nahAMin: coerceString(parsed.nahAMin, this.nahAMin),
        nahAMax: coerceString(parsed.nahAMax, this.nahAMax),
        nahHMin: coerceString(parsed.nahHMin, this.nahHMin),
        nahHMax: coerceString(parsed.nahHMax, this.nahHMax),
        casalUnidadeMin: coerceString(parsed.casalUnidadeMin, this.casalUnidadeMin),
        casalUnidadeMax: coerceString(parsed.casalUnidadeMax, this.casalUnidadeMax),
        qdlsFilters: coerceRangeArray(parsed.qdlsFilters, this.defaultQdls),
        unitFilters: coerceRangeArray(parsed.unitFilters, this.defaultUnits),
        tenFilters: coerceRangeArray(parsed.tenFilters, this.defaultTens),
        limit,
        offset
      };
    } catch (err) {
      console.warn('Falha ao ler filtros salvos.', err);
      return null;
    }
  }

  private getStorage(): Storage | null {
    if (typeof window === 'undefined') {
      return null;
    }
    try {
      return window.localStorage;
    } catch (err) {
      console.warn('Falha ao acessar o armazenamento local.', err);
      return null;
    }
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
    setRange(this.casalUnidadeMin, this.casalUnidadeMax, 'unitPairsMin', 'unitPairsMax');

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
