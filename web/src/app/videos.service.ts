import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, map, Observable, of } from 'rxjs';
import { ParseFuncsService } from './parse-funcs.service';
import { IVideoList } from './server-settings';

@Injectable({
  providedIn: 'root'
})
export class VideosService {

  private readonly CHANNEL_API_URL = '/api/channel-videos/'

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
}


