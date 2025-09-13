import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppComponent } from './app.component';
import { ResultsListComponent } from './components/results-list/results-list.component';
import { TresPorLinhaListComponent } from './components/tres-por-linha-list/tres-por-linha-list.component';
import { AppRoutingModule } from './app-routing.module';
import { SelectorComponent } from './components/selector/selector.component';
import { SelectorByFiltersComponent } from './components/selector-by-filters/selector-by-filters.component';


@NgModule({
  declarations: [
    AppComponent,
    ResultsListComponent,
    TresPorLinhaListComponent,
    SelectorComponent,
    SelectorByFiltersComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    AppRoutingModule,
    FormsModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
