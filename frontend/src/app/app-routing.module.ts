import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ResultsListComponent } from './components/results-list/results-list.component';

const routes: Routes = [
  { path: '', redirectTo: '/results', pathMatch: 'full' },
  { path: 'results', component: ResultsListComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule {}
