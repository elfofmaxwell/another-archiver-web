import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, Observable } from 'rxjs';
import { ParseFuncsService } from './parse-funcs.service';
import { ErrorMessage, IScanned, Settings } from './server-settings';

@Injectable({
  providedIn: 'root'
})
export class SettingsService {

  private readonly SETTINGS_URL = '/api/settings';
  private readonly SCAN_URL = '/api/scan-local';

  constructor(
    private http: HttpClient, 
    private parseFuncs: ParseFuncsService
  ) { }


  getSettings(): Observable<Settings|ErrorMessage> {
    return this.http.get<Settings>(this.SETTINGS_URL)
    .pipe(
      catchError(
        this.parseFuncs.parseHttpError
      )
    );
  }


  putSettings(settingObj: Settings): Observable<Settings|ErrorMessage> {
    return this.http.put<Settings>(this.SETTINGS_URL, settingObj)
    .pipe(
      catchError(
        this.parseFuncs.parseHttpError
      )
    );
  }

  
  scanLocalFiles(): Observable<IScanned|ErrorMessage> {
    return this.http.get<IScanned>(this.SCAN_URL)
    .pipe(
      catchError(
        this.parseFuncs.parseHttpError
      )
    );
  }
}
