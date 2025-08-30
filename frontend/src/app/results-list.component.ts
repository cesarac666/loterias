import { Component, OnInit } from '@angular/core';
import { ResultsService, LotofacilResult } from './results.service';

@Component({
  selector: 'app-results-list',
  templateUrl: './results-list.component.html',
  styleUrls: ['./results-list.component.css']
})
export class ResultsListComponent implements OnInit {
  results: LotofacilResult[] = [];

  constructor(private resultsService: ResultsService) {}

  ngOnInit(): void {
    this.resultsService.getLastResults().subscribe(r => this.results = r);
  }
}
