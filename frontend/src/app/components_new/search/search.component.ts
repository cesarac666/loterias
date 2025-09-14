import { Component } from '@angular/core';
//import { FiltragemService } from '../../services/filtragem.service';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
// import { BrowserModule } from '@angular/platform-browser';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './search.component.html',
  styleUrl: './search.component.css',
})
export class SearchComponent {
  opcaoSelecionada: number = 1;

  constructor(
    private router: Router //,
  ) //private filtragemService: FiltragemService
  {}

  onBuscar(): void {
    console.log('Entrou em onBuscar');
    //this.filtragemService.mudarOpcaoFiltragem(this.opcaoSelecionada);
    this.router.navigate(['/home/load', this.opcaoSelecionada]);
  }
}
