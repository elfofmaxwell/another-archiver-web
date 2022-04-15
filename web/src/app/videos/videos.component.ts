import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-videos',
  templateUrl: './videos.component.html',
  styleUrls: ['./videos.component.css']
})
export class VideosComponent implements OnInit {

  constructor(
    private router: Router
  ) { }

  queryType: 'videos' | 'search' = 'videos';
  reloadToggle: boolean = false;

  ngOnInit(): void {
    const searchRe = /search*/;
    const _queryType = this.router.url.split('/')[1];
    if (searchRe.test(_queryType)) {
      this.queryType = 'search';
    }
  }

  onReloadVideos(): void {
    this.reloadToggle = !this.reloadToggle;
  }
}
