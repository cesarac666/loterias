import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';

@Component({
  selector: 'app-dia-da-sorte-ticket',
  templateUrl: './dia-da-sorte-ticket.component.html',
  styleUrls: ['./dia-da-sorte-ticket.component.css']
})
export class DiaDaSorteTicketComponent implements OnChanges {
  @Input() numerosSorteados: number[] = [];

  readonly numeros = Array.from({ length: 31 }, (_, i) => i + 1);
  private selecionados: boolean[] = new Array(31).fill(false);

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['numerosSorteados']) {
      this.marcarNumerosSorteados();
    }
  }

  private marcarNumerosSorteados(): void {
    this.selecionados.fill(false);
    if (!Array.isArray(this.numerosSorteados)) {
      return;
    }
    this.numerosSorteados.forEach((numero) => {
      if (Number.isInteger(numero) && numero >= 1 && numero <= 31) {
        this.selecionados[numero - 1] = true;
      }
    });
  }

  isSelecionado(numero: number): boolean {
    if (numero < 1 || numero > 31) {
      return false;
    }
    return this.selecionados[numero - 1];
  }
}
