import { Component } from '@angular/core';
import { FilterService } from './filter.service';

interface FilterOption {
  label: string;
  value: string;
  checked: boolean;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  datasets = [
    { label: 'Últimos 500', value: 'ultimos500_lotofacil_05062023.csv' },
    { label: 'Todas 3 por Linha', value: 'todasTresPorLinha.csv' }
  ];
  selectedDataset = this.datasets[0].value;

  filterOptions: FilterOption[] = [
    { label: 'Resultados Anteriores', value: 'filtroResultadosAnteriores', checked: false },
    { label: 'Quase Três por Linha', value: 'filtroQuaseTresPorLinha', checked: false },
    { label: 'Quase Três por Linha Fixo', value: 'filtroQuaseTresPorLinhaFixo', checked: false },
    { label: 'Três por Linha', value: 'filtroTresPorLinha', checked: false },
    { label: 'Dezenas Pares Ímpares', value: 'filtroDezenasParesImpares', checked: false },
    { label: 'Dezena Sem Colunas Repetidas', value: 'filtroDezenaSemColunasSequenciasRepetidas', checked: false },
    { label: 'Filtro Apostas N', value: 'filtroApostasN', checked: false },
    { label: 'Frequência de Dezenas', value: 'filtroFrequenciaDezenas', checked: false },
    { label: 'Filtra Apostas NAH', value: 'filtraApostasNAH', checked: false }
  ];

  constructor(private filterService: FilterService) {}

  applyFilters() {
    const activeFilters = this.filterOptions
      .filter(opt => opt.checked)
      .map(opt => opt.value);
    this.filterService.applyFilters(this.selectedDataset, activeFilters)
      .subscribe(result => console.log('Filtered results', result));
  }
}
