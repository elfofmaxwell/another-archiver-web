import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { TagData } from 'ngx-tagify';
import { catchError, map, Observable, of } from 'rxjs';
import { ParseFuncsService } from './parse-funcs.service';
import { AddedVideoDetail, IVideoList } from './server-settings';

@Injectable({
  providedIn: 'root'
})
export class VideosService {

  private readonly CHANNEL_API_URL = '/api/channel-videos/';
  private readonly GET_HEX_ID_URL = '/api/get-new-hex-vid';
  private readonly GET_TAG_SUGGESTION_URL = '/api/get-tag-suggestion';
  private readonly MANNUALLY_ADD_VIDEO_URL = '/api/manually-add-video';

  constructor(
    private http: HttpClient,
    private parseFuncs: ParseFuncsService
  ) { }

  getChannelVideos(channelId: string, page: number, pageEntryNum: number=5): Observable<IVideoList> {
    const queryUrl = `${this.CHANNEL_API_URL}${channelId}?`;
    const queryParams = new HttpParams({fromObject: {page: page,pageEntryNum: pageEntryNum}});
    return this.http.get<IVideoList>(`${queryUrl}${queryParams}`)
    .pipe(
      catchError(
        () => of({videoNum: 0, videoList: []})
      ), 
      // format iso8601 upload date and durations
      map(
        (videoList: IVideoList): IVideoList => {
          for (let video of videoList.videoList) {
            video.uploadDate = this.parseFuncs.formatIsoDate(video.uploadDate);
            video.duration = this.parseFuncs.formatIsoDuration(video.duration);
          }
          return videoList;
        }
      )
    );
  }

  // get unique id for adding unarchived content
  getHexId (): Observable<string> {
    return this.http.get<string>(this.GET_HEX_ID_URL)
    .pipe(
      catchError(
        () => of('')
      )
    );
  }

  getTagSuggestion (queryType: 'talents' | 'tags', queryStr: string): Observable<TagData[]> {
    const queryURL = `${this.GET_TAG_SUGGESTION_URL}?`
    const queryParams = new HttpParams({fromObject: {tagType: queryType, queryStr: queryStr}});
    return this.http.get<string[]>(queryURL+queryParams)
    .pipe(
      catchError(
        ()=>of([])
      ), 
      map(
        (suggestionStrs: string[]) => {
          const suggestions: TagData[] = [];
          for (let suggestionStr of suggestionStrs) {
            suggestions.push({value: suggestionStr});
          }
          return suggestions;
        }
      )
    );
  }

  manuallyAddVideo (videoId: string='', unarchivedContent: boolean=false, title: string='', uploadDate: string='', duration: string='', thumbUrl: string='', channelId: string='', talentNames: string[]=[], stream_types: string[]=[]): Observable<AddedVideoDetail> {
    return this.http.post<AddedVideoDetail>(this.MANNUALLY_ADD_VIDEO_URL, {
      videoId: videoId, 
      unarchivedContent: unarchivedContent,
      title: title, 
      uploadDate: uploadDate, 
      duration: duration, 
      thumbUrl: thumbUrl, 
      channelId: channelId, 
      talentNames: talentNames, 
      stream_types: stream_types
    }).pipe(
      catchError(
        ()=>{
          let emptyAddedVideoDetail = new AddedVideoDetail();
          emptyAddedVideoDetail.serverMessage = 'Server error.';
          return of(emptyAddedVideoDetail);
        }
      )
    );
  }
}


