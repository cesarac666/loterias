import { Component, OnInit } from '@angular/core';
import { StartService } from '../../services/start.service';

@Component({
  selector: 'app-statistcs',
  standalone: true,
  imports: [],
  templateUrl: './statistcs.component.html',
  styleUrl: './statistcs.component.css',
})
export class StatistcsComponent implements OnInit {
  mensagem = '';

  constructor(private dadosService: StartService) {}

  ngOnInit(): void {
    this.dadosService.getMensagem().subscribe((data: string) => {
      this.mensagem = data;
    });
  }
}
