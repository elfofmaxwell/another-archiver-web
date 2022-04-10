import { Component, Input, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { IVideoList } from '../server-settings';
import { VideosService } from '../videos.service';

@Component({
  selector: 'app-video-list',
  templateUrl: './video-list.component.html',
  styleUrls: ['./video-list.component.css']
})
export class VideoListComponent implements OnInit {

  constructor(
    private route: ActivatedRoute, 
    private videosService: VideosService, 
    private router: Router
  ) { }
  
  @Input() pageSize: number = 5;
  channelVideos: IVideoList = {videoNum: 0, videoList: []};
  pageNum: number = 0;
  private _page: number = 1;
  jumpToPage: number = 1;
  get page(): number {
    return this._page;
  }
  set page(value: number) {
    this._page = value;
    this.jumpToPage = value;
    this.getVideos(value, this.pageSize);
  }

  ngOnInit(): void {
    this.getVideos(this.page, this.pageSize);
  }

  getVideos(page: number, pageEntryNum: number): void {
    if (this.router.url.split('/')[1] === 'channel') {
      const channelId = this.route.snapshot.paramMap.get('channelId'); 
      if (channelId) {
        this.videosService.getChannelVideos(channelId, page, pageEntryNum).subscribe(
          (videoList) => {
            this.channelVideos = videoList;
            this.pageNum = Math.ceil(videoList.videoNum/this.pageSize);
          }
        );
      }
    }
  }

  jumpTo() {
    const jumpToPage = this.jumpToPage;
    if (jumpToPage <= 0) {
      this.page = 1;
    } else if (jumpToPage > this.pageNum) {
      this.page = this.pageNum;
    } else {
      this.page = jumpToPage;
    }
  }
}
