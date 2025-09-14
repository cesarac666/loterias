import { Component, OnInit } from '@angular/core';
import { LoadService } from '../../services/load.service';
import { CommonModule } from '@angular/common';
import { LottoticketComponent } from '../lottoticket/lottoticket.component';
//import { FiltragemService } from '../../services/filtragem.service';
import { ActivatedRoute, Router } from '@angular/router';
import { LottotabularComponent } from '../lottotabular/lottotabular.component';

type NomedeFiltros = {
  [key: number]: string;
};

@Component({
  selector: 'app-load',
  standalone: true,
  imports: [CommonModule, LottoticketComponent, LottotabularComponent],
  templateUrl: './load.component.html',
  styleUrl: './load.component.css',
})
export class LoadComponent implements OnInit {
  ultimosSorteados: any[] = [];
  concursos: number[] = [];
  nomeFiltro: string = '';
  totalRegistros: number = 0;

  constructor(
    //private filtragemService: FiltragemService,
    private route: ActivatedRoute,
    private loadDataService: LoadService,
    private router: Router
  ) {}

  ngOnInit(): void {
    console.log('ngOnInit no LoadComponent:');

    var opcao = 1;

    this.route.params.subscribe((params) => {
      opcao = +params['opcao'];
      //this.filtragemService.opcaoFiltragemAtual.subscribe((opcao) => {
      console.log('Opção de Filtragem recebida no LoadComponent:', opcao);

      this.loadDataService.getLoadData(opcao).subscribe((data) => {
        console.log('Dados recebidos do backend:', data);

        this.ultimosSorteados = data.map((sorteio) =>
          this.extrairNumerosSorteados(sorteio)
        );
      });
    });

    console.log('AQUI LEN=' + this.concursos.length);
    // this.atualizarDados(this.concursos, opcao);
    this.atualizarDados(opcao);
  }

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

  // Suponha que esta função é chamada quando os dados são recebidos
  atualizarDados(
    // sorteios: any[],
    opcaoFiltragem: number
  ): void {
    this.ultimosSorteados = this.concursos;
    this.totalRegistros = this.concursos.length;

    // Atualize esta lógica conforme necessário para mapear opcaoFiltragem para o nome do filtro
    const nomesFiltros: NomedeFiltros = {
      1: 'Filtro 1',
      2: 'Filtro 2',
      3: 'Filtro 3',
    };
    this.nomeFiltro = nomesFiltros[opcaoFiltragem] || 'Filtro Desconhecido';
  }

  goBack(): void {
    this.router.navigate(['/home']);
    // ou
    // window.history.back();
  }
}
