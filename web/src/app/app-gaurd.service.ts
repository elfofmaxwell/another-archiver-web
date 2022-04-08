import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot, UrlTree } from '@angular/router';
import { map, Observable } from 'rxjs';
import { AuthService } from './auth.service';
import { IUser } from './server-settings';

@Injectable({
  providedIn: 'root'
})
export class AppGaurdService implements CanActivate {

  constructor(private router: Router, private authService: AuthService) { }

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean | UrlTree | Observable<boolean | UrlTree> | Promise<boolean | UrlTree> {
    return this.authService.checkLogin().pipe(
      map((user: IUser) => {
        if (user.userName) {
          return true;
        } else {
          return false;
        }
      })
    );
  }
}
