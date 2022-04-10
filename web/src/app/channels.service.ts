import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, map, Observable, of } from 'rxjs';
import { ParseFuncsService } from './parse-funcs.service';
import { ChannelDetail, ChannelOverview, ChannelStats } from './server-settings';


@Injectable({
  providedIn: 'root'
})
export class ChannelsService {

  private readonly GET_CHANNEL_LIST_URL = '/api/channels';
  private readonly ADD_CHANNEL_URL = '/api/add-channel';
  private readonly FETCH_CHANNELS_URL = '/api/fetch-channels';
  private readonly GET_CHANNEL_DETAIL_URL = '/api/channel/';
  private readonly GET_CHANNEL_STATS_URL = '/api/channel-stats';

  constructor(
    private http: HttpClient, 
    private parseFuncsService: ParseFuncsService
  ) { }

  // channel list services
  getChannelList (): Observable<ChannelOverview[]> {
    return this.http.get<ChannelOverview[]>(this.GET_CHANNEL_LIST_URL)
    .pipe(
      catchError(
        () => {
          const emptyList: ChannelOverview[] = [];
          return of(emptyList);
        }
      )
    );
  }

  addYouTubeChannel (channelId: string): Observable<ChannelOverview> {
    const addChannelRequestBody = {channelId: channelId};
    return this.http.post<ChannelOverview>(this.ADD_CHANNEL_URL, addChannelRequestBody)
    .pipe(
      catchError(
        () => {
          const emptyChannel = new ChannelOverview(); 
          return of(emptyChannel);
        }
      )
    );
  }

  fetchAllChannel (): Observable<ChannelOverview[]> {
    return this.http.get<ChannelOverview[]>(this.FETCH_CHANNELS_URL)
    .pipe(
      catchError(
        () => {
          const emptyList: ChannelOverview[] = [];
          return of(emptyList);
        }
      )
    );
  }

  // single channel services
  getChannelDetail (channelId: string): Observable<ChannelDetail> {
    return this.http.get<ChannelDetail>(this.GET_CHANNEL_DETAIL_URL+channelId)
    .pipe(
      catchError(
        () => {
          const emptyChannelDetail = new ChannelDetail;
          return of(emptyChannelDetail);
        }
      )
    );
  }

  // get channel stats
  getChannelStats (channelId: string, timeDelta: number=0, lowerDateStamp: string='', upperDateStamp: string=''): Observable<ChannelStats> {
    const queryUrl = `${this.GET_CHANNEL_STATS_URL}?`;
    const queryParams = new HttpParams({fromObject: {channelId: channelId, timeDelta: timeDelta, lowerDateStamp: lowerDateStamp, upperDateStamp: upperDateStamp, statsType: 'all'}});
    return this.http.get<ChannelStats>(queryUrl+queryParams)
    .pipe(
      catchError(
        () => {
          return of(new ChannelStats());
        }
      ), 
      map(
        (channelStats: ChannelStats) => {
          channelStats.videoNumStats.week = channelStats.videoNumStats.week.map((isoDate)=>this.parseFuncsService.formatIsoDate(isoDate, 'YY-MM-DD'));
          channelStats.durationStats.week = channelStats.durationStats.week.map((isoDate)=>this.parseFuncsService.formatIsoDate(isoDate, 'YY-MM-DD'));
          channelStats.durationStats.duration = channelStats.durationStats.duration.map((durationSec: number)=>Number((durationSec/3600).toFixed(2)));
          return channelStats;
        }
      )
    );
  }
}
