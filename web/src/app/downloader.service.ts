import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, Observable } from 'rxjs';
import { ParseFuncsService } from './parse-funcs.service';
import { ErrorMessage, IDownloading } from './server-settings';

@Injectable({
  providedIn: 'root'
})
export class DownloaderService {

  private readonly DOWNLOADING_URL = '/api/downloading';
  private readonly DOWNLOAD_VIDEO_URL = '/api/download/'

  constructor(
    private http: HttpClient, 
    private parseFuncs: ParseFuncsService
  ) { }

  checkDownloading(): Observable<IDownloading|ErrorMessage> {
    return this.http.get<IDownloading>(this.DOWNLOADING_URL)
    .pipe(
      catchError(
        this.parseFuncs.parseHttpError
      )
    );
  }

  downloadSingleVideo(videoId: string): Observable<IDownloading|ErrorMessage> {
    const queryUrl = this.DOWNLOAD_VIDEO_URL+videoId;
    return this.http.get<IDownloading>(queryUrl)
    .pipe(
      catchError(
        this.parseFuncs.parseHttpError
      )
    );
  }
}
