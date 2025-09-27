import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

import { AppComponent } from './app.component';
import { ResultsListComponent } from './components/results-list/results-list.component';
import { TresPorLinhaListComponent } from './components/tres-por-linha-list/tres-por-linha-list.component';
import { AppRoutingModule } from './app-routing.module';
import { LottoticketComponent } from './components_new/lottoticket/lottoticket.component';
import { SelectorComponent } from './components/selector/selector.component';
import { SelectorByFiltersComponent } from './components/selector-by-filters/selector-by-filters.component';
import { DiaDaSorteListComponent } from './components/dia-da-sorte-list/dia-da-sorte-list.component';
import { DiaDaSorteTicketComponent } from './components/dia-da-sorte-ticket/dia-da-sorte-ticket.component';
import { DiaDaSorteBetsComponent } from './components/dia-da-sorte-bets/dia-da-sorte-bets.component';

@NgModule({
  declarations: [
    AppComponent,
    ResultsListComponent,
    TresPorLinhaListComponent,
    SelectorComponent,
    SelectorByFiltersComponent,
    DiaDaSorteListComponent,
    DiaDaSorteTicketComponent,
    DiaDaSorteBetsComponent
  ],
  imports: [
    BrowserModule,
    HttpClientModule,
    AppRoutingModule,
    FormsModule,
    LottoticketComponent
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
