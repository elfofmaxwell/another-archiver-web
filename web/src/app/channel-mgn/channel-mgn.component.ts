import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, ViewChild } from '@angular/core';
import { NgForm } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { TagData, TagifySettings } from 'ngx-tagify';
import { Observable, Subject } from 'rxjs';
import {
  debounceTime, distinctUntilChanged, switchMap
} from 'rxjs/operators';
import { ChannelsService } from '../channels.service';
import { IMessage, MessageService } from '../message.service';
import { ParseFuncsService } from '../parse-funcs.service';
import { AddedVideoDetail, ChannelDetail } from '../server-settings';
import { VideosService } from '../videos.service';

@Component({
  selector: 'app-channel-mgn',
  templateUrl: './channel-mgn.component.html',
  styleUrls: ['./channel-mgn.component.css']
})
export class ChannelMgnComponent implements OnChanges {

  @Input() channelDetail: ChannelDetail = new ChannelDetail();
  @Output() requestReload = new EventEmitter();
  
  constructor(
    private videosService: VideosService, 
    private channelsService: ChannelsService, 
    public messageService: MessageService, 
    private route: ActivatedRoute, 
    private parseFuncs: ParseFuncsService
  ) { }

  channelId = this.route.snapshot.paramMap.get('channelId');

  // messages
  messageList: IMessage[] = [];

  // upload index
  newDownloadIdx: number | undefined = undefined;
  newIdAsIdx: string | undefined = undefined;
  offset: number | undefined = undefined;
  newIdxFormValid: boolean = false;
  updateNewIdxForValid(): void {
    this.newIdxFormValid = ((this.newDownloadIdx || this.newDownloadIdx === 0) || this.newIdAsIdx || this.offset) ? true : false;
  }
  @ViewChild('newIdxForm') newIdxForm?: NgForm;
  updateIdx() {
    if (((this.newDownloadIdx || this.newDownloadIdx === 0) || this.newIdAsIdx || this.offset) && this.channelId) {
      this.channelsService.updateDownloadIdx(
        this.channelId, 
        this.newDownloadIdx ? this.newDownloadIdx : 0, 
        this.newIdAsIdx ? this.newIdAsIdx : '', 
        this.offset ? this.offset : 0
      ).subscribe(
        (channelDetail: ChannelDetail) => {
          if (channelDetail.channelId) {
            this.messageService.setSingleMessage(this.messageList, `Download Index has been updated to ${channelDetail.checkpointIndex}`, 'success');
            this.newIdxForm?.reset();
            this.requestReload.emit();
          } else {
            this.messageService.setSingleMessage(this.messageList, 'Sorry, updating download index failed', 'danger');
          }
        }
      );
    }
  }

  
  //new talent name
  newChannelTalentName: string = '';
  @ViewChild('addChannelTalentForm') addChannelTalentForm?: NgForm;
  addChannelTalentName(): void {
    if (this.channelId) {
      this.channelsService.addChannelTalentName(this.channelId, this.newChannelTalentName)
      .subscribe(
        (channelDetail: ChannelDetail) => {
          if (channelDetail.channelId) {
            this.messageService.setSingleMessage(this.messageList, `Talent name updated to ${channelDetail.talentName}`, 'success');
            this.addChannelTalentForm?.reset();
          } else {
            this.messageService.setSingleMessage(this.messageList, 'Sorry, updating talent name failed', 'danger');
          }
        }
      );
    }
  }
  addVideoTalentName(): void {
    if (this.channelId) {
      this.channelsService.addTalentNameForVideos(this.channelId)
      .subscribe(
        (channelDetail:ChannelDetail) => {
          if (channelDetail.channelId) {
            this.messageService.setSingleMessage(this.messageList, `Videos without talent tag now have tag ${channelDetail.talentName}`, 'success');
          } else {
            this.messageService.setSingleMessage(this.messageList, 'Sorry, adding talent name for videos failed', 'danger');
          }
        }
      );
    }
  }

  // add video manually
  @ViewChild('newVideoForm') newVideoForm?: NgForm;
  unarchivedContent: boolean = false;
  toggleUnarchivedContent (): void {
    if (this.unarchivedContent) {
      this.newVideoId = '';
      this.unarchivedContent = false;
    } else {
      this.videosService.getHexId().subscribe((newHexId)=>{this.newVideoId=newHexId});
      this.unarchivedContent = true;
    }
  }
  newVideoId: string = '';
  newVideoTitle: string = '';
  _newVideoUploadTime: string = '';
  set newVideoUploadTime(uploadTime: string) {
    this._newVideoUploadTime = uploadTime+':00Z';
  }
  get newVideoUploadTime(): string {
    return this._newVideoUploadTime.substring(0, this._newVideoUploadTime.length-4);
  }
  newVideoDuration: string = '';
  newVideoThumb: string = '';
  talentTags: TagData[] = [];
  talentTagSettings: TagifySettings = {
    callbacks: {
     input: (e) => {this.talentSuggestionTerm.next(e.detail.value);}
    }
  };
  talentSuggestionTerm = new Subject<string>();
  talentWhitelist$: Observable<TagData[]> = this.talentSuggestionTerm.pipe(
    debounceTime(300), 
    switchMap((talentInputStr: string) => this.videosService.getTagSuggestion("talents", talentInputStr))
  );
  inputValue: string = '';
  streamTypeTags: TagData[] = [];
  
  streamTypeTagSettings: TagifySettings = {
    callbacks: {
     input: (e) => {this.streamTypeSuggestionTerm.next(e.detail.value);}
    }
  };
  streamTypeSuggestionTerm = new Subject<string>();
  streamTypeWhitelist$: Observable<TagData[]> = this.streamTypeSuggestionTerm.pipe(
    debounceTime(300), 
    distinctUntilChanged(), 
    switchMap((streamTypeInputStr: string) => this.videosService.getTagSuggestion("tags", streamTypeInputStr))
  );
  onManuallyAddVideo(): void {
    const _talentTags: string[] = [];
    const _streamTypeTags: string[] = [];
    const _newVideoDuration = this.parseFuncs.toIsoDuration(this.newVideoDuration);
    for (let talentTag of this.talentTags) {
      _talentTags.push(talentTag.value);
    }
    for (let streamTypeTag of this.streamTypeTags) {
      _streamTypeTags.push(streamTypeTag.value);
    }
    this.videosService.manuallyAddVideo(this.newVideoId, this.unarchivedContent, this.newVideoTitle, this._newVideoUploadTime, _newVideoDuration, this.newVideoThumb, this.channelId?this.channelId:'', _talentTags, _streamTypeTags)
    .subscribe(
      (addedVideoDetail: AddedVideoDetail) => {
        if ((addedVideoDetail.serverMessage === undefined) && addedVideoDetail.videoId) {
          this.messageService.setSingleMessage(this.messageList, `Video ${addedVideoDetail.videoId}: ${addedVideoDetail.title} has been added.`, 'success');
          this.newVideoForm?.reset();
          if (this.unarchivedContent) {
            this.videosService.getHexId().subscribe((newHexId)=>{this.newVideoId=newHexId});
          }
          this.talentTags = [];
          this.streamTypeTags = [];
          this.requestReload.emit();
        } else if(typeof addedVideoDetail.serverMessage === 'string') {
          this.messageService.setSingleMessage(this.messageList, addedVideoDetail.serverMessage, 'danger');
        } else {
          this.messageService.setSingleMessage(this.messageList, 'Oops, something went wrong', 'danger');
        }
      }
    );
  }


  // when channel detail changed, refresh component
  ngOnChanges(changes: SimpleChanges): void {
    this.newChannelTalentName = this.channelDetail.talentName;
  }
}
