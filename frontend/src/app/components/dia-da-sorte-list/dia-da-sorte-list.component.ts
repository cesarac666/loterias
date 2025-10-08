import { Component, OnInit } from '@angular/core';
import { DiaDaSorteService, DiaDaSorteResult } from '../../services/dia-da-sorte.service';

type RangeField = { min: number; max: number };
type DigitProfile = 'quente' | 'fria' | 'neutra';

interface ValueSummary {
  min: number;
  max: number;
  mode: number | null;
}

interface NahSummary {
  n: ValueSummary | null;
  a: ValueSummary | null;
  h: ValueSummary | null;
}

interface DigitSummary {
  units: Record<string, ValueSummary | null>;
  tens: Record<string, ValueSummary | null>;
}

interface DigitFrequency {
  total: number;
  average: number;
  profile: DigitProfile;
}

interface DigitFrequencySummary {
  units: Record<string, DigitFrequency>;
  tens: Record<string, DigitFrequency>;
  overallUnitsAverage: number;
  overallTensAverage: number;
}

interface SummaryStats {
  pares: ValueSummary | null;
  impares: ValueSummary | null;
  maxConsec: ValueSummary | null;
  maiorSalto: ValueSummary | null;
  ganhadores7: ValueSummary | null;
  isolatedCount: ValueSummary | null;
  nah: NahSummary;
  qdls: (ValueSummary | null)[];
  digitStats: DigitSummary;
  digitFrequency: DigitFrequencySummary;
}

interface SummaryTracker {
  min: number;
  max: number;
  counts: Map<number, number>;
}

@Component({
  selector: 'app-dia-da-sorte-list',
  templateUrl: './dia-da-sorte-list.component.html',
  styleUrls: ['./dia-da-sorte-list.component.css']
})
export class DiaDaSorteListComponent implements OnInit {
  results: DiaDaSorteResult[] = [];
  total = 0;
  limit = 20;
  loading = false;
  updating = false;
  error?: string;
  updateStatus?: string;
  updateError?: string;
  selectedTicketNumbers: number[] | null = null;
  showPrintPreview = false;
  summary: SummaryStats | null = null;

  readonly monthLabels = [
    '',
    'Janeiro',
    'Fevereiro',
    'Marco',
    'Abril',
    'Maio',
    'Junho',
    'Julho',
    'Agosto',
    'Setembro',
    'Outubro',
    'Novembro',
    'Dezembro'
  ];

  readonly unitDigits = Array.from({ length: 10 }, (_, i) => String(i));
  readonly tenDigits = Array.from({ length: 4 }, (_, i) => String(i));

  constructor(private readonly diaDaSorteService: DiaDaSorteService) {}

  ngOnInit(): void {
    this.loadResults();
  }

  loadResults(): void {
    const effectiveLimit = this.limit && this.limit > 0 ? this.limit : undefined;
    this.loading = true;
    this.error = undefined;
    this.diaDaSorteService.getResults(effectiveLimit).subscribe({
      next: (response) => {
        this.results = response.results;
        this.total = response.total;
        this.loading = false;
        this.computeSummary(this.results);
      },
      error: (err) => {
        console.error('Falha ao carregar Dia da Sorte', err);
        this.results = [];
        this.summary = null;
        this.error = 'Falha ao carregar resultados do Dia da Sorte.';
        this.loading = false;
      }
    });
  }

  refreshResultsAndStats(): void {
    if (this.updating || this.loading) {
      return;
    }
    this.updating = true;
    this.updateStatus = undefined;
    this.updateError = undefined;
    this.diaDaSorteService.updateResultsAndStats().subscribe({
      next: (response) => {
        const fallback =
          response.count > 0
            ? `Atualizados ${response.count} concurso(s).`
            : 'Nenhum novo concurso encontrado.';
        this.updateStatus = response.message || fallback;
        this.loadResults();
      },
      error: (err) => {
        console.error('Falha ao atualizar resultados do Dia da Sorte', err);
        this.updateError = 'Falha ao atualizar resultados e estatisticas.';
        this.updating = false;
      },
      complete: () => {
        this.updating = false;
      }
    });
  }

  trackByConcurso(index: number, item: DiaDaSorteResult): number {
    return item.concurso;
  }

  getMonthLabel(month: number): string {
    return this.monthLabels[month] ?? String(month);
  }

  formatNah(result: DiaDaSorteResult): string {
    const { nahN, nahA, nahH } = result;
    if (nahN == null || nahA == null || nahH == null) {
      return 'N/A';
    }
    return `${nahN}-${nahA}-${nahH}`;
  }

  formatQdls(result: DiaDaSorteResult): string {
    const valores = Array.isArray(result.qdls) ? result.qdls : [];
    if (!valores.length) {
      return '-';
    }
    return valores
      .map((quantidade, indice) => `S${indice + 1}=${quantidade}`)
      .join(', ');
  }

  formatDigitStats(result: DiaDaSorteResult): string {
    const stats = result.digitStats;
    if (!stats) {
      return 'N/A';
    }
    const formatGrupo = (prefixo: string, mapa: Record<string, number>): string => {
      const partes = Object.entries(mapa)
        .filter(([, quantidade]) => quantidade > 0)
        .map(([digito, quantidade]) => `${prefixo}${digito}=${quantidade}`);
      return partes.length ? partes.join(', ') : `${prefixo}-`;
    };
    return `${formatGrupo('U', stats.units)} | ${formatGrupo('D', stats.tens)}`;
  }

  formatSummaryValue(summary?: ValueSummary | null): string {
    if (!summary || !Number.isFinite(summary.min) || !Number.isFinite(summary.max)) {
      return '-';
    }
    const range = summary.min === summary.max ? `${summary.min}` : `${summary.min} - ${summary.max}`;
    if (summary.mode == null) {
      return range;
    }
    return `${range} (moda ${summary.mode})`;
  }

  formatNahSummary(summary?: NahSummary | null): string {
    if (!summary) {
      return '-';
    }
    const partes = [
      `N=${this.formatSummaryValue(summary.n)}`,
      `A=${this.formatSummaryValue(summary.a)}`,
      `H=${this.formatSummaryValue(summary.h)}`
    ];
    return partes.join(' | ');
  }

  formatQdlsSummary(summaries?: (ValueSummary | null)[] | null): string {
    if (!summaries?.length) {
      return '-';
    }
    return summaries
      .map((summary, index) => `S${index + 1}=${this.formatSummaryValue(summary)}`)
      .join(', ');
  }

  formatDigitStatsSummary(summary?: DigitSummary | null): string {
    if (!summary) {
      return '-';
    }
    const formatMap = (prefixo: string, mapa: Record<string, ValueSummary | null>): string => {
      const partes: string[] = [];
      for (const chave of Object.keys(mapa).sort((a, b) => Number(a) - Number(b))) {
        partes.push(`${prefixo}${chave}=${this.formatSummaryValue(mapa[chave])}`);
      }
      return partes.join(', ');
    };
    return `${formatMap('U', summary.units)} | ${formatMap('D', summary.tens)}`;
  }

  formatAverage(value: number): string {
    return value.toFixed(2);
  }

  profileLabel(profile: DigitProfile): string {
    switch (profile) {
      case 'quente':
        return 'Quente';
      case 'fria':
        return 'Fria';
      default:
        return 'Neutra';
    }
  }

  profileClass(profile: DigitProfile): string {
    return `profile-${profile}`;
  }

  showTicket(result: DiaDaSorteResult): void {
    this.selectedTicketNumbers = result.bolas;
  }

  clearSelectedTicket(): void {
    this.selectedTicketNumbers = null;
  }

  openPrintPreview(): void {
    this.showPrintPreview = true;
  }

  closePrintPreview(): void {
    this.showPrintPreview = false;
  }

  printTicket(): void {
    window.print();
  }

  printAll(): void {
    window.print();
  }

  private createTracker(): SummaryTracker {
    return { min: Number.POSITIVE_INFINITY, max: Number.NEGATIVE_INFINITY, counts: new Map<number, number>() };
  }

  private updateTracker(tracker: SummaryTracker, value: number | null | undefined): void {
    if (value == null || Number.isNaN(value)) {
      return;
    }
    tracker.min = Math.min(tracker.min, value);
    tracker.max = Math.max(tracker.max, value);
    tracker.counts.set(value, (tracker.counts.get(value) || 0) + 1);
  }

  private finalizeTracker(tracker: SummaryTracker): ValueSummary | null {
    if (tracker.counts.size === 0 || !Number.isFinite(tracker.min) || !Number.isFinite(tracker.max)) {
      return null;
    }
    let modeValue: number | null = null;
    let modeCount = -1;
    for (const [value, count] of tracker.counts.entries()) {
      if (count > modeCount || (count === modeCount && (modeValue === null || value < modeValue))) {
        modeValue = value;
        modeCount = count;
      }
    }
    return { min: tracker.min, max: tracker.max, mode: modeValue };
  }

  private computeSummary(results: DiaDaSorteResult[]): void {
    if (!results.length) {
      this.summary = null;
      return;
    }

    const paresTracker = this.createTracker();
    const imparesTracker = this.createTracker();
    const maxConsecTracker = this.createTracker();
    const maiorSaltoTracker = this.createTracker();
    const isolatedTracker = this.createTracker();
    const ganhadoresTracker = this.createTracker();
    const nahNTracker = this.createTracker();
    const nahATracker = this.createTracker();
     const nahHTracker = this.createTracker();

    const qdlsLength = results[0].qdls?.length ?? 0;
    const qdlsTrackers = Array.from({ length: qdlsLength }, () => this.createTracker());

    const unitTrackers: Record<string, SummaryTracker> = {};
    const tenTrackers: Record<string, SummaryTracker> = {};
    this.unitDigits.forEach((key) => {
      unitTrackers[key] = this.createTracker();
    });
    this.tenDigits.forEach((key) => {
      tenTrackers[key] = this.createTracker();
    });

    const unitTotals: Record<string, number> = {};
    const tenTotals: Record<string, number> = {};
    this.unitDigits.forEach((key) => {
      unitTotals[key] = 0;
    });
    this.tenDigits.forEach((key) => {
      tenTotals[key] = 0;
    });

    results.forEach((item) => {
      this.updateTracker(paresTracker, item.pares);
      this.updateTracker(imparesTracker, item.impares);
      this.updateTracker(maxConsecTracker, item.maxConsec);
      this.updateTracker(maiorSaltoTracker, item.maiorSalto);
      this.updateTracker(isolatedTracker, item.isolatedCount);
      this.updateTracker(ganhadoresTracker, item.ganhadores7Acertos);

      if (item.nahN != null) {
        this.updateTracker(nahNTracker, item.nahN);
      }
      if (item.nahA != null) {
        this.updateTracker(nahATracker, item.nahA);
      }
      if (item.nahH != null) {
        this.updateTracker(nahHTracker, item.nahH);
      }

      if (item.qdls?.length === qdlsTrackers.length) {
        item.qdls.forEach((valor, indice) => {
          this.updateTracker(qdlsTrackers[indice], valor);
        });
      }

      const stats = item.digitStats;
      if (stats) {
        this.unitDigits.forEach((key) => {
          const valor = stats.units?.[key] ?? 0;
          this.updateTracker(unitTrackers[key], valor);
          unitTotals[key] += valor;
        });
        this.tenDigits.forEach((key) => {
          const valor = stats.tens?.[key] ?? 0;
          this.updateTracker(tenTrackers[key], valor);
          tenTotals[key] += valor;
        });
      }
    });

    const concursos = results.length;
    const totalUnits = this.unitDigits.reduce((acc, key) => acc + unitTotals[key], 0);
    const totalTens = this.tenDigits.reduce((acc, key) => acc + tenTotals[key], 0);
    const overallUnitsAvg = totalUnits / this.unitDigits.length / concursos;
    const overallTensAvg = totalTens / this.tenDigits.length / concursos;

    const digitFrequency: DigitFrequencySummary = {
      units: {},
      tens: {},
      overallUnitsAverage: overallUnitsAvg,
      overallTensAverage: overallTensAvg
    };

    this.unitDigits.forEach((key) => {
      const total = unitTotals[key];
      const average = total / concursos;
      digitFrequency.units[key] = {
        total,
        average,
        profile: this.classifyDigit(average, overallUnitsAvg)
      };
    });

    this.tenDigits.forEach((key) => {
      const total = tenTotals[key];
      const average = total / concursos;
      digitFrequency.tens[key] = {
        total,
        average,
        profile: this.classifyDigit(average, overallTensAvg)
      };
    });

    this.summary = {
      pares: this.finalizeTracker(paresTracker),
      impares: this.finalizeTracker(imparesTracker),
      maxConsec: this.finalizeTracker(maxConsecTracker),
      maiorSalto: this.finalizeTracker(maiorSaltoTracker),
      isolatedCount: this.finalizeTracker(isolatedTracker),
      ganhadores7: this.finalizeTracker(ganhadoresTracker),
      nah: {
        n: this.finalizeTracker(nahNTracker),
        a: this.finalizeTracker(nahATracker),
        h: this.finalizeTracker(nahHTracker)
      },
      qdls: qdlsTrackers.map((tracker) => this.finalizeTracker(tracker)),
      digitStats: {
        units: Object.fromEntries(this.unitDigits.map((key) => [key, this.finalizeTracker(unitTrackers[key])])),
        tens: Object.fromEntries(this.tenDigits.map((key) => [key, this.finalizeTracker(tenTrackers[key])]))
      },
      digitFrequency
    };
  }

  private classifyDigit(avg: number, baseline: number): DigitProfile {
    const tolerance = 0.2;
    if (avg > baseline + tolerance) {
      return 'quente';
    }
    if (avg < baseline - tolerance) {
      return 'fria';
    }
    return 'neutra';
  }
}
