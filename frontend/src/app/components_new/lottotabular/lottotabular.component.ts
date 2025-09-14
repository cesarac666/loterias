import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'app-lottotabular',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './lottotabular.component.html',
  styleUrl: './lottotabular.component.css',
})
export class LottotabularComponent implements OnInit {
  @Input() numerosSorteados: number[][] = [];

  constructor() {}

  ngOnInit(): void {}
}
