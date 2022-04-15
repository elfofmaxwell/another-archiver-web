import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { IMessage, MessageService } from '../message.service';
import { ParseFuncsService } from '../parse-funcs.service';
import { SearchService } from '../search.service';
import { ErrorMessage, IQueryObj, IVideoList } from '../server-settings';
import { VideosService } from '../videos.service';

@Component({
  selector: 'app-video-list',
  templateUrl: './video-list.component.html',
  styleUrls: ['./video-list.component.css']
})
export class VideoListComponent implements OnChanges {

  constructor(
    private route: ActivatedRoute, 
    private videosService: VideosService, 
    private router: Router, 
    private parseFuncs: ParseFuncsService, 
    private messageService: MessageService, 
    private searchService: SearchService
  ) { }
  
  @Input() queryType: "videos" | "search" | "channel" = 'videos';
  @Input() pageSize: number = 5;
  messageList: IMessage[] = [];

  videosOnPage: IVideoList = {videoNum: 0, videoList: []};
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

  @Input() reloadTrigger: boolean = false;
  ngOnChanges(changes: SimpleChanges): void {
    this.getVideos(this.page, this.pageSize);
  }

  processVideoList: (videoList: IVideoList|ErrorMessage)=>void = (videoList) => {
    if (videoList instanceof ErrorMessage) {
      this.messageService.setSingleMessage(this.messageList, videoList.message, 'danger');
    } else {
      this.messageService.clearMessage(this.messageList);
      this.videosOnPage = videoList;
      for (let videoOverview of this.videosOnPage.videoList) {
        videoOverview.uploadDate = this.parseFuncs.formatIsoDate(videoOverview.uploadDate); 
        videoOverview.duration = this.parseFuncs.formatIsoDuration(videoOverview.duration);
      }
      this.pageNum = Math.ceil(videoList.videoNum/this.pageSize);
    }
  }

  getVideos(page: number, pageEntryNum: number): void {
    if (this.queryType === "channel") {
      const channelId = this.route.snapshot.paramMap.get('channelId'); 
      if (channelId) {
        this.videosService.getChannelVideos(channelId, page, pageEntryNum).subscribe(
          this.processVideoList
        );
      }
    } else if (this.queryType === 'videos') {
      this.videosService.getAllVideos(page, pageEntryNum).subscribe(
        this.processVideoList
      );
    } else {
      const urlParams = this.route.snapshot.queryParamMap; 
      const queryObj: IQueryObj = this.searchService.urlToQueryObj(urlParams);
      queryObj['page'] = page;
      const queryStr = this.searchService.objToBackendQueryString(queryObj);
      this.videosService.getSearchedVideos(queryStr).subscribe(
        this.processVideoList
      );
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

  goToVideo(videoId: string) {
    this.router.navigate(['/video', videoId]);
  }
}
