import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { TagData } from 'ngx-tagify';
import { catchError, map, Observable, of } from 'rxjs';
import { ParseFuncsService } from './parse-funcs.service';
import { AddedVideoDetail, ErrorMessage, IVideoList, VideoDetail } from './server-settings';

@Injectable({
  providedIn: 'root'
})
export class VideosService {

  private readonly SINGLE_VIDEO_URL = '/api/video/';
  private readonly ALL_VIDEO_URL = '/api/videos';
  private readonly CHANNEL_API_URL = '/api/channel-videos/';
  private readonly GET_HEX_ID_URL = '/api/get-new-hex-vid';
  private readonly GET_TAG_SUGGESTION_URL = '/api/get-tag-suggestion';
  private readonly MANUALLY_ADD_VIDEO_URL = '/api/manually-add-video';
  private readonly MANUALLY_UPDATE_VIDEO_URL = '/api/manually-update-video/';
  private readonly ADD_SINGLE_VIDEO_TALENT_URL = '/api/add-talent/';
  private readonly ADD_SINGLE_VIDEO_TYPE_URL = '/api/add-stream-type/';
  private readonly DELETE_VIDEO_URL = '/api/delete-video/';
  private readonly SEARCH_VIDEO_URL = '/api/search'

  constructor(
    private http: HttpClient,
    private parseFuncs: ParseFuncsService
  ) { }
  
  getSingleVideo(videoId: string): Observable<VideoDetail|ErrorMessage> {
    return this.http.get<VideoDetail>(this.SINGLE_VIDEO_URL+videoId)
    .pipe(
      catchError(
        this.parseFuncs.parseHttpError
      )
    );
  }
  

  getChannelVideos(channelId: string, page: number, pageEntryNum: number=5): Observable<IVideoList|ErrorMessage> {
    const queryUrl = `${this.CHANNEL_API_URL}${channelId}?`;
    const queryParams = new HttpParams({fromObject: {page: page,pageEntryNum: pageEntryNum}});
    return this.http.get<IVideoList>(`${queryUrl}${queryParams}`)
    .pipe(
      catchError(
        this.parseFuncs.parseHttpError
      )
    );
  }


  getAllVideos(page: number, pageEntryNum: number=10): Observable<IVideoList|ErrorMessage> {
    const queryParams = new HttpParams({fromObject: {page: page,pageEntryNum: pageEntryNum}});
    return this.http.get<IVideoList>(this.ALL_VIDEO_URL+`?${queryParams}`)
    .pipe(
      catchError(
        this.parseFuncs.parseHttpError
      )
    );
  }


  getSearchedVideos(queryStr: HttpParams): Observable<IVideoList|ErrorMessage> {
    const queryUrl = this.SEARCH_VIDEO_URL+`?${queryStr}`;
    return this.http.get<IVideoList>(queryUrl)
    .pipe(
      catchError(
        this.parseFuncs.parseHttpError
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
    return this.http.post<AddedVideoDetail>(this.MANUALLY_ADD_VIDEO_URL, {
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


  manuallyUpdateVideo (videoId: string='', title: string='', uploadDate: string='', duration: string='', channelId: string='', thumbUrl: string=''): Observable<VideoDetail|ErrorMessage> {
    const queryUrl = this.MANUALLY_UPDATE_VIDEO_URL+videoId;
    return this.http.post<VideoDetail>(queryUrl, {
      title: title, 
      uploadDate: uploadDate, 
      duration: duration, 
      channelId: channelId, 
      thumbUrl: thumbUrl
    }).pipe(
      catchError(
        this.parseFuncs.parseHttpError
      )
    )
  }


  addSingleVideoTalents (videoId: string, talentNames: string[]): Observable<VideoDetail|ErrorMessage> {
    const queryUrl = this.ADD_SINGLE_VIDEO_TALENT_URL + videoId
    return this.http.post<VideoDetail>(queryUrl, talentNames)
    .pipe(
      catchError(
        this.parseFuncs.parseHttpError
      )
    );
  }


  addSingleVideoTypes (videoId: string, streamTypes: string[]): Observable<VideoDetail|ErrorMessage> {
    const queryUrl = this.ADD_SINGLE_VIDEO_TYPE_URL + videoId
    return this.http.post<VideoDetail>(queryUrl, streamTypes)
    .pipe(
      catchError(
        this.parseFuncs.parseHttpError
      )
    );
  }


  deleteVideo (videoId: string): Observable<VideoDetail|ErrorMessage> {
    const queryUrl = this.DELETE_VIDEO_URL + videoId;
    return this.http.delete<VideoDetail>(queryUrl)
    .pipe(
      catchError(
        this.parseFuncs.parseHttpError
      )
    );
  }
}


