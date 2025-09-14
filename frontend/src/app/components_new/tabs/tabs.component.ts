import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { HelloComponent } from '../../hello/hello.component';
import { SearchComponent } from '../search/search.component';
import { Router, RouterModule } from '@angular/router';

@Component({
  selector: 'app-tabs',
  standalone: true,
  imports: [CommonModule, HelloComponent, SearchComponent, RouterModule],
  templateUrl: './tabs.component.html',
  styleUrl: './tabs.component.css',
})
export class TabsComponent {
  selectedTab = 1;

  //selectTab(tabIndex: number): void {
  //  this.selectedTab = tabIndex;
  //}
  constructor(private router: Router) {}

  selectTab(tabIndex: number): void {
    this.selectedTab = tabIndex;
    const routes = [
      '/home/start', //1
      '/home/search', //2
      '/home/bets', //3
      '/home/tpl', //4
      '/home/hello', //5,
    ];
    this.router.navigate([routes[tabIndex - 1]]);
  }
}
