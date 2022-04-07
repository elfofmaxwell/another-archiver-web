import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, Observable, of, tap } from 'rxjs';
import { IUser, LoginInfo, SERVERURL } from './server-settings';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  constructor(
    private http: HttpClient
  ) { }

  user: IUser = {
    userId: -1, 
    userName: ''
  };

  private handleLoginError (): Observable<IUser> {
    return of({
      userId: -1, 
      userName: '',
    });
  }

  checkLogin (): Observable<IUser> {
    if (this.user.userName) {
      return of(this.user);
    } else {
      return this.http.get<IUser>(SERVERURL+'/api/check-login')
      .pipe(
        catchError(this.handleLoginError)
      );
    }
  }

  logIn (loginInfo: LoginInfo): Observable<IUser> {
    console.log(loginInfo);
    return this.http.post<IUser>(SERVERURL+'/api/login', loginInfo)
    .pipe(
      catchError(this.handleLoginError), 
      tap((user) => {
        this.user = user;
      })
    );
  }
}
