import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, Observable, of } from 'rxjs';
import { ChannelOverview } from './server-settings';


@Injectable({
  providedIn: 'root'
})
export class ChannelsService {

  private readonly GET_CHANNEL_LIST_URL = '/api/channels';
  private readonly ADD_CHANNEL_URL = '/api/add-channel';
  private readonly FETCH_CHANNELS_URL = 'api/fetch-channels';

  constructor(
    private http: HttpClient
  ) { }

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
}
