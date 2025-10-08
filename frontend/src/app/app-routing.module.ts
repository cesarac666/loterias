import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ResultsListComponent } from './components/results-list/results-list.component';
import { TresPorLinhaListComponent } from './components/tres-por-linha-list/tres-por-linha-list.component';
import { SelectorComponent } from './components/selector/selector.component';
import { SelectorByFiltersComponent } from './components/selector-by-filters/selector-by-filters.component';
import { DiaDaSorteListComponent } from './components/dia-da-sorte-list/dia-da-sorte-list.component';
import { DiaDaSorteBetsComponent } from './components/dia-da-sorte-bets/dia-da-sorte-bets.component';
import { DiaDaSorteSavedBetsComponent } from './components/dia-da-sorte-saved-bets/dia-da-sorte-saved-bets.component';

const routes: Routes = [
  { path: '', redirectTo: '/results', pathMatch: 'full' },
  { path: 'results', component: ResultsListComponent },
  { path: 'tres-por-linha', component: TresPorLinhaListComponent },
  { path: 'selecionar', component: SelectorComponent },
  { path: 'selecionar-por-filtros', component: SelectorByFiltersComponent },
  { path: 'dia-da-sorte', component: DiaDaSorteListComponent },
 { path: 'dia-da-sorte-apostas', component: DiaDaSorteBetsComponent },
 { path: 'dia-da-sorte-conferencia', component: DiaDaSorteSavedBetsComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}
