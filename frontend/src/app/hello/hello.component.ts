import { Component, OnInit } from '@angular/core';
import { HelloxService } from '../services/hellox.service';

@Component({
  selector: 'app-hello',
  standalone: true,
  imports: [],
  templateUrl: './hello.component.html',
  styleUrl: './hello.component.css',
})
export class HelloComponent implements OnInit {
  mensagem = '';

  constructor(private dadosService: HelloxService) {}

  ngOnInit() {
    this.dadosService.getMensagem().subscribe((data: string) => {
      this.mensagem = data;
    });
  }
}
