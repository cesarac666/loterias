import { Component, OnInit } from '@angular/core';
import { StartService } from '../../services/start.service';
import { CommonModule } from '@angular/common';
import { LottoticketComponent } from '../lottoticket/lottoticket.component';

@Component({
  selector: 'app-start',
  standalone: true,
  imports: [CommonModule, LottoticketComponent],
  templateUrl: './start.component.html',
  styleUrl: './start.component.css',
})
export class StartComponent implements OnInit {
  mensagem = '';
  ultimos: any[] = [];
  ultimosSorteados: any[] = [];
  concursos: number[] = [];

  constructor(private dadosService: StartService) {}

  ngOnInit(): void {
    this.dadosService.getLoadData().subscribe((data) => {
      this.ultimos = data; // Aqui você já está populando a lista de resultados corretamente

      this.ultimosSorteados = data.map((sorteio) =>
        this.extrairNumerosSorteados(sorteio)
      );
    });
  }

  // -----------------------------------------------------------------------------------
  extrairNumerosSorteados(sorteio: any): number[] {
    const numerosSorteados: number[] = [];

    this.extrairNumeroConcurso(sorteio);

    // Loop de B1 até B15
    for (let i = 1; i <= 15; i++) {
      const chave = `B${i}`; // Monta a chave (B1, B2, ..., B15)
      const valor = sorteio[chave];

      // Verifica se o valor é um número e está entre 1 e 25
      if (typeof valor === 'number' && valor >= 1 && valor <= 25) {
        numerosSorteados.push(valor);
      }
    }
    console.log('numerosSorteados:' + numerosSorteados);
    return numerosSorteados;
  }

  extrairNumeroConcurso(sorteio: any): number {
    const cc = `CC`;
    const numCC = sorteio[cc];

    console.log('CC=' + numCC);

    this.concursos.push(numCC);

    console.log('LEN=' + this.concursos.length);

    return numCC;
  }

  // -----------------------------------------------------------------------------------
}
