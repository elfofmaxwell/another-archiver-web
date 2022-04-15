import { Location } from '@angular/common';
import { Component, OnInit, ViewChild } from '@angular/core';
import { NgForm } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { TagData, TagifySettings } from 'ngx-tagify';
import { Observable, Subject } from 'rxjs';
import {
  debounceTime, distinctUntilChanged, switchMap
} from 'rxjs/operators';
import { AuthService } from '../auth.service';
import { DownloaderService } from '../downloader.service';
import { IMessage, MessageService } from '../message.service';
import { ParseFuncsService } from '../parse-funcs.service';
import { ErrorMessage, IDownloading, VideoDetail } from '../server-settings';
import { VideosService } from '../videos.service';
@Component({
  selector: 'app-single-video',
  templateUrl: './single-video.component.html',
  styleUrls: ['./single-video.component.css']
})
export class SingleVideoComponent implements OnInit {

  constructor(
    public authService: AuthService, 
    private route: ActivatedRoute, 
    private videosService: VideosService, 
    private parseFuncs: ParseFuncsService, 
    private messageService: MessageService, 
    private location: Location, 
    private downloaderService: DownloaderService, 
    private modalService: NgbModal
  ) { }
  
  videoId = this.route.snapshot.paramMap.get('videoId');
  manageVideoToggle: boolean = false;
  editTalentToggle: boolean = false;
  editStreamTypeToggle: boolean = false;
  messageList: IMessage[] = [];
  downloaderStatus: boolean = true;

  videoDetail: VideoDetail = new VideoDetail();
  unarchivedContent: boolean = false;
  _videoUploadDate: string = '';
  _videoDuration: string = '';


  // play video
  get videoUrlWithTime(): string {
    return encodeURIComponent(this.videoDetail.localPath);
  }
  openModal(modalContent: any) {
    this.modalService.open(
      modalContent, 
      {
        centered: true,
        size: 'lg',
      }
    )
  }


  // talent tags
  talentTags: TagData[] = [];
  talentTagSettings: TagifySettings = {
    callbacks: {
     input: (e) => {this.talentSuggestionTerm.next(e.detail.value);}
    }
  };
  talentSuggestionTerm = new Subject<string>();
  talentWhitelist$: Observable<TagData[]> = this.talentSuggestionTerm.pipe(
    debounceTime(100), 
    switchMap((talentInputStr: string) => this.videosService.getTagSuggestion("talents", talentInputStr))
  );
  onAddTalentTags() {
    if (this.videoId) {
      this.videosService.addSingleVideoTalents(this.videoId, this.parseFuncs.tagDataListToList(this.talentTags))
      .subscribe(
        (addTagResult)=>{
          if (addTagResult instanceof ErrorMessage) {
            this.messageService.setSingleMessage(this.messageList, addTagResult.message, 'warning');
          } else {
            this.messageService.clearMessage(this.messageList);
            this.videoDetail = addTagResult;
            this.editTalentToggle = false;
          }
        }
      );
    }
  }

  // stream type tags
  streamTypeTags: TagData[] = [];
  streamTypeTagSettings: TagifySettings = {
    callbacks: {
     input: (e) => {this.streamTypeSuggestionTerm.next(e.detail.value);}
    }
  };
  streamTypeSuggestionTerm = new Subject<string>();
  streamTypeWhitelist$: Observable<TagData[]> = this.streamTypeSuggestionTerm.pipe(
    debounceTime(100), 
    distinctUntilChanged(), 
    switchMap((streamTypeInputStr: string) => this.videosService.getTagSuggestion("tags", streamTypeInputStr))
  );
  onAddTypeTags() {
    if (this.videoId) {
      this.videosService.addSingleVideoTypes(this.videoId, this.parseFuncs.tagDataListToList(this.streamTypeTags))
      .subscribe(
        (addTagResult)=>{
          if (addTagResult instanceof ErrorMessage) {
            this.messageService.setSingleMessage(this.messageList, addTagResult.message, 'danger');
          } else {
            this.messageService.clearMessage(this.messageList);
            this.videoDetail = addTagResult;
            this.editStreamTypeToggle = false;
          }
        }
      );
    }
  }


  // manage video
  @ViewChild('updateVideoForm') updateVideoForm?: NgForm;
  newChannelId: string = '';
  newTitle: string = '';
  newUploadTime?:string;
  newDuration: string = '';
  newThumbUrl: string = '';
  onUpdateVideo(): void {
    if (this.videoId) {
      const _newUploadTime: string = this.newUploadTime ? this.parseFuncs.toIsoDateTimeUTC(this.newUploadTime) : '';
      const _newDuration: string = this.newDuration ? this.parseFuncs.toIsoDuration(this.newDuration) : '';
      this.videosService.manuallyUpdateVideo(this.videoId, this.newTitle, _newUploadTime, _newDuration, this.newChannelId, this.newThumbUrl).subscribe(
        (updateResult: VideoDetail|ErrorMessage)=>{
          if (updateResult instanceof ErrorMessage) {
            this.messageService.setSingleMessage(this.messageList, updateResult.message, 'danger');
          } else {
            this.messageService.clearMessage(this.messageList); 
            this.videoDetail = updateResult; 
            this._videoUploadDate = this.parseFuncs.formatIsoDate(this.videoDetail.uploadDate, 'MMM DD, YYYY HH:mm');
            this._videoDuration = this.parseFuncs.formatIsoDuration(this.videoDetail.duration);
            this.updateVideoForm?.reset();
          }
        }
      )
    }
  }


  // delete video
  onDeleteVideo() {
    if (this.videoId) {
      if (!confirm('Are you sure you want delete this video? This action would not influence local video file.')) {
        return;
      }
      this.videosService.deleteVideo(this.videoId)
      .subscribe(
        (deleteResult: VideoDetail|ErrorMessage) => {
          if (deleteResult instanceof ErrorMessage) {
            this.messageService.setSingleMessage(this.messageList, deleteResult.message, 'danger'); 
          } else {
            this.location.back();
          }
        }
      )
    }
  }


  // download video
  onDownloadVideo() {
    if (this.videoId) {
      this.downloaderService.downloadSingleVideo(this.videoId)
      .subscribe(
        (downloadTriggerResult: IDownloading|ErrorMessage)=>{
          if (downloadTriggerResult instanceof ErrorMessage) {
            this.messageService.setSingleMessage(this.messageList, downloadTriggerResult.message, 'danger');
          } else {
            this.downloaderStatus = downloadTriggerResult.downloading;
            if (downloadTriggerResult.downloading) {
              this.messageService.setSingleMessage(this.messageList, 'Downloader started', 'success');
            } else {
              this.messageService.setSingleMessage(this.messageList, 'Starting downloader failed', 'danger');
            }
          }
        }
      )
    }
  }


  ngOnInit(): void {
    this.authService.checkLogin();
    this.getVideoDetail();
    if (this.authService.user.userName) {
      this.checkDownloader();
    }
  }

  getVideoDetail() {
    if (this.videoId) {
      this.videosService.getSingleVideo(this.videoId)
      .subscribe(
        (videoDetail: VideoDetail|ErrorMessage)=>{
          if (videoDetail instanceof ErrorMessage) {
            this.messageService.setSingleMessage(this.messageList, videoDetail.message, 'danger')
          } else {
            this.videoDetail = videoDetail;
            this.unarchivedContent = (this.videoDetail.videoId.substring(0, 2) === '__') && (this.videoDetail.videoId.substring(this.videoDetail.videoId.length-2) === '__');
            this._videoUploadDate = this.parseFuncs.formatIsoDate(this.videoDetail.uploadDate, 'MMM DD, YYYY HH:mm');
            this._videoDuration = this.parseFuncs.formatIsoDuration(this.videoDetail.duration);
            this.talentTags = this.parseFuncs.listToTagDataList(this.videoDetail.talentNames);
            this.streamTypeTags = this.parseFuncs.listToTagDataList(this.videoDetail.streamTypes);
          }
        }
      );
    }
  }
  
  checkDownloader() {
    this.downloaderService.checkDownloading()
    .subscribe(
      (checkResult: IDownloading|ErrorMessage) => {
        if (checkResult instanceof ErrorMessage) {
          this.messageService.setSingleMessage(this.messageList, checkResult.message, 'danger');
        } else {
          this.messageService.clearMessage(this.messageList);
          this.downloaderStatus = checkResult.downloading;
        }
      }
    );
  }
}
