import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ResultsListComponent } from './components/results-list/results-list.component';
import { TresPorLinhaListComponent } from './components/tres-por-linha-list/tres-por-linha-list.component';

const routes: Routes = [
  { path: '', redirectTo: '/results', pathMatch: 'full' },
  { path: 'results', component: ResultsListComponent },
  { path: 'tres-por-linha', component: TresPorLinhaListComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}
