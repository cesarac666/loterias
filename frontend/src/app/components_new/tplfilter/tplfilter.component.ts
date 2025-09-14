import { Component, OnInit } from '@angular/core';
import { CemMilService } from '../../services/cemmil.service';

@Component({
  selector: 'app-tplfilter',
  standalone: true,
  imports: [],
  templateUrl: './tplfilter.component.html',
  styleUrl: './tplfilter.component.css',
})
export class TplfilterComponent implements OnInit {
  mensagem = 'Filtros T p l';

  constructor(private dadosService: CemMilService) {}

  ngOnInit() {
    this.dadosService.getMensagem().subscribe((data: string) => {
      this.mensagem = data;
    });
  }
}
