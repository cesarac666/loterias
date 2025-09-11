import { Component, OnInit, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { ResultsService, LotofacilResult, ResultsResponse } from '../../results.service';

@Component({
  selector: 'app-results-list',
  templateUrl: './results-list.component.html',
  styleUrls: ['./results-list.component.css']
})
export class ResultsListComponent implements OnInit, AfterViewInit {
  results: LotofacilResult[] = [];
  useParImpar = false;
  pares = '';
  impares = '';
  concursoLimite = '';
  totalRegistros = 0;

  @ViewChild('patternChart') canvasRef!: ElementRef<HTMLCanvasElement>;

  constructor(private resultsService: ResultsService) {}

  ngOnInit(): void {
    this.loadResults();
  }

  loadResults(): void {
    const paresVals = this.pares
      .replace(/;/g, ',')
      .split(',')
      .map(v => parseInt(v.trim(), 10))
      .filter(v => !isNaN(v));
    const imparesVals = this.impares
      .replace(/;/g, ',')
      .split(',')
      .map(v => parseInt(v.trim(), 10))
      .filter(v => !isNaN(v));
    const pares = this.useParImpar ? paresVals : [];
    const impares = this.useParImpar ? imparesVals : [];
    const limiteVal = parseInt(this.concursoLimite, 10);
    const limite = isNaN(limiteVal) ? undefined : limiteVal;
    this.resultsService
      .getLastResults(pares, impares, limite)
      .subscribe((r: ResultsResponse) => {
        this.results = r.results;
        this.totalRegistros = r.total;
        this.drawChart();
      });
  }

  ngAfterViewInit(): void {
    this.drawChart();
  }

  drawChart(): void {
    const canvas = this.canvasRef?.nativeElement;
    if (!canvas) {
      return;
    }
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      return;
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const sorted = [...this.results].sort((a, b) => a.concurso - b.concurso);

    const patterns = ['3 por linha', 'quase 3 por linha', '1 linha completa', 'outro'];
    const colors = ['#007bff', '#28a745', '#dc3545', '#ffc107'];
    const series: number[][] = patterns.map(() => []);
    const counts = new Array(patterns.length).fill(0);
    sorted.forEach(r => {
      let idx = patterns.indexOf(r.padraoLinha);
      if (idx === -1) {
        idx = patterns.indexOf('outro');
      }
      counts[idx] += 1;
      patterns.forEach((_, i) => series[i].push(counts[i]));
    });
    const maxY = Math.max(1, ...series.flat());
    const stepX = sorted.length > 1 ? canvas.width / (sorted.length - 1) : canvas.width;

    const scaleY = (canvas.height - 30) / maxY;

    patterns.forEach((_, i) => {
      ctx.beginPath();
      ctx.strokeStyle = colors[i];
      series[i].forEach((y, j) => {
        const x = j * stepX;
        const yPos = canvas.height - y * scaleY - 20;

        if (j === 0) {
          ctx.moveTo(x, yPos);
        } else {
          ctx.lineTo(x, yPos);
        }
      });
      ctx.stroke();
      series[i].forEach((y, j) => {
        const x = j * stepX;
        const yPos = canvas.height - y * scaleY - 20;
        ctx.fillStyle = colors[i];
        ctx.beginPath();
        ctx.arc(x, yPos, 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#fff';
        ctx.fillText(String(y), x + 5, yPos - 5);
      });
      
    let lx = 10, ly = 10;
    patterns.forEach((p, i) => {
      ctx.fillStyle = colors[i];
      ctx.fillRect(lx, ly - 8, 10, 10);
      ctx.fillStyle = '#fff';

      ctx.fillText(p, lx + 15, ly);
      ly += 15;
    });
  }
}
