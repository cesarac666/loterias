import { Component, OnInit } from '@angular/core';
import {
  DiaDaSorteService,
  DiaDaSorteSavedBet
} from '../../services/dia-da-sorte.service';

interface SummaryEntry {
  label: string;
  value: number;
}

@Component({
  selector: 'app-dia-da-sorte-saved-bets',
  templateUrl: './dia-da-sorte-saved-bets.component.html',
  styleUrls: ['./dia-da-sorte-saved-bets.component.css']
})
export class DiaDaSorteSavedBetsComponent implements OnInit {
  bets: DiaDaSorteSavedBet[] = [];
  total = 0;
  loading = false;
  deleting = false;
  submitting = false;
  error?: string;
  status?: string;
  concursoFiltro = '';
  aguardandoResultado = 0;
  resumo: SummaryEntry[] = [];
  ordenarPorAcertosDesc = true;
  private pendingStatusMessage?: string;

  constructor(private readonly diaDaSorteService: DiaDaSorteService) {}

  ngOnInit(): void {
    this.loadSavedBets();
  }

  loadSavedBets(): void {
    if (this.loading || this.submitting) {
      return;
    }
    this.loading = true;
    this.error = undefined;
    this.status = undefined;
    this.bets = [];
    this.total = 0;
    this.resumo = [];
    this.aguardandoResultado = 0;

    const concurso = this.parseConcurso(this.concursoFiltro);
    this.diaDaSorteService.getSavedBets(concurso).subscribe({
      next: (response) => {
        this.bets = response.results;
        this.applySorting();
        this.total = response.total;
        this.computeSummary();
        this.loading = false;
        if (this.pendingStatusMessage) {
          this.status = this.pendingStatusMessage;
          this.pendingStatusMessage = undefined;
        } else if (response.total === 0) {
          this.status = 'Nenhuma aposta armazenada para o filtro informado.';
        }
      },
      error: (err) => {
        console.error('Falha ao carregar apostas salvas', err);
        this.error = 'Falha ao carregar apostas salvas.';
        this.loading = false;
        this.pendingStatusMessage = undefined;
      }
    });
  }

  clearFilter(): void {
    if (!this.concursoFiltro) {
      this.loadSavedBets();
      return;
    }
    this.concursoFiltro = '';
    this.loadSavedBets();
  }

  formatResultado(bet: DiaDaSorteSavedBet): string {
    if (!bet.resultadoDisponivel || !bet.resultado) {
      return 'Aguardando resultado';
    }
    return bet.resultado.join(', ');
  }

  formatAcertos(bet: DiaDaSorteSavedBet): string {
    if (!bet.resultadoDisponivel || bet.acertos == null) {
      return 'Aguardando';
    }
    return `${bet.acertos}`;
  }

  trackById(index: number, item: DiaDaSorteSavedBet): number {
    return item.id;
  }

  toggleSortByHits(): void {
    this.ordenarPorAcertosDesc = !this.ordenarPorAcertosDesc;
    this.applySorting();
  }

  deleteSavedBets(): void {
    if (this.loading || this.deleting || this.submitting) {
      return;
    }
    const concurso = this.parseConcurso(this.concursoFiltro);
    const mensagemAlvo = concurso
      ? `Excluir todas as apostas do concurso ${concurso}?`
      : 'Excluir todas as apostas salvas?';
    const confirmado = typeof window !== 'undefined' ? window.confirm(mensagemAlvo) : true;
    if (!confirmado) {
      return;
    }
    this.deleting = true;
    this.error = undefined;
    const alvo = concurso ?? null;
    this.diaDaSorteService.deleteSavedBets(concurso).subscribe({
      next: (response) => {
        const deleted = response.deleted ?? 0;
        const alvoConcurso = response.concurso ?? alvo;
        const message =
          deleted > 0
            ? `Excluidas ${deleted} aposta(s)${alvoConcurso ? ` do concurso ${alvoConcurso}` : ''}.`
            : `Nenhuma aposta excluida${alvoConcurso ? ` para o concurso ${alvoConcurso}` : ''}.`;
        this.pendingStatusMessage = message;
        this.deleting = false;
        this.loadSavedBets();
      },
      error: (err) => {
        console.error('Falha ao excluir apostas salvas', err);
        this.error = 'Falha ao excluir apostas salvas.';
        this.deleting = false;
      }
    });
  }

  private applySorting(): void {
    const factor = this.ordenarPorAcertosDesc ? -1 : 1;
    this.bets = [...this.bets].sort((a, b) => {
      const acertosA = a.acertos ?? -1;
      const acertosB = b.acertos ?? -1;
      if (acertosA !== acertosB) {
        return (acertosA - acertosB) * factor;
      }
      if (a.concurso !== b.concurso) {
        return (a.concurso - b.concurso) * factor;
      }
      return (a.id - b.id) * factor;
    });
  }

  private computeSummary(): void {
    const mapa: Record<string, number> = {};
    let aguardando = 0;
    for (const bet of this.bets) {
      if (bet.resultadoDisponivel && bet.acertos != null) {
        const key = `${bet.acertos}`;
        mapa[key] = (mapa[key] ?? 0) + 1;
      } else {
        aguardando += 1;
      }
    }
    this.aguardandoResultado = aguardando;
    this.resumo = Object.entries(mapa)
      .sort((a, b) => Number(b[0]) - Number(a[0]))
      .map(([label, value]) => ({ label, value }));
  }

  private parseConcurso(value: string): number | undefined {
    const trimmed = value?.trim();
    if (!trimmed) {
      return undefined;
    }
    const num = Number(trimmed);
    return Number.isFinite(num) ? num : undefined;
  }

  submitBetsOnline(): void {
    if (this.loading || this.deleting || this.submitting) {
      return;
    }
    const concurso = this.parseConcurso(this.concursoFiltro);
    this.submitting = true;
    this.error = undefined;
    this.status = undefined;
    this.diaDaSorteService.submitSavedBets(concurso).subscribe({
      next: (response) => {
        this.status = response.message;
        this.submitting = false;
      },
      error: (err) => {
        console.error('Falha ao iniciar envio automatico de apostas', err);
        this.error = 'Falha ao iniciar envio automatico de apostas.';
        this.submitting = false;
      }
    });
  }
}
