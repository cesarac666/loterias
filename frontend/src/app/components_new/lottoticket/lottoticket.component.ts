import { CommonModule } from '@angular/common';
import {
  Component,
  Input,
  OnChanges,
  OnInit,
  SimpleChanges,
} from '@angular/core';

@Component({
  selector: 'app-lottoticket',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './lottoticket.component.html',
  styleUrl: './lottoticket.component.css',
})
export class LottoticketComponent implements OnChanges {
  //implements OnInit {
  // V1

  numerosSelecionados: boolean[] = new Array(25).fill(false);

  generateArray(n: number): number[] {
    return [...Array(n).keys()];
  }

  toggleNumero(i: number): void {
    this.numerosSelecionados[i - 1] = !this.numerosSelecionados[i - 1];
  }

  simularSorteio(): void {
    this.numerosSelecionados.fill(false); // Reseta a seleção atual
    let sorteados: Set<number> = new Set();
    while (sorteados.size < 15) {
      // Gera um número aleatório entre 1 e 25
      const sorteado = Math.floor(Math.random() * 25) + 1;
      sorteados.add(sorteado);
    }
    // Marca os números sorteados como selecionados
    sorteados.forEach((num) => {
      this.numerosSelecionados[num - 1] = true;
    });
  }

  limparSorteio(): void {
    this.numerosSelecionados.fill(false);
  }

  // V2
  @Input() numerosSorteados: number[] = [];

  // numerosSelecionados: boolean[] = new Array(25).fill(false);

  // ngOnInit(): void {
  //  this.marcarNumerosSorteados();
  // }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['numerosSorteados']) {
      this.marcarNumerosSorteados();
    }
  }

  marcarNumerosSorteados(): void {
    this.numerosSelecionados.fill(false); // Reseta antes de marcar
    this.numerosSorteados.forEach((num) => {
      this.numerosSelecionados[num - 1] = true;
    });
  }
}
