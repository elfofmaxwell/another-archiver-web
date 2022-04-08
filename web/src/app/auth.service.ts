import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, Observable, of, tap } from 'rxjs';
import { IUser, LoginInfo } from './server-settings';

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
      return this.http.get<IUser>('/api/check-login')
      .pipe(
        catchError(this.handleLoginError), 
        tap((user) => this.user = user)
      );
    }
  }

  logIn (loginInfo: LoginInfo): Observable<IUser> {
    return this.http.post<IUser>('/api/login', loginInfo)
    .pipe(
      catchError(this.handleLoginError), 
      tap((user) => {
        this.user = user;
      })
    );
  }

  logOut (): Observable<IUser> {
    return this.http.get<IUser>('/api/logout')
    .pipe(
      tap((user) => {
        this.user = user;
      })
    );
  }
}
