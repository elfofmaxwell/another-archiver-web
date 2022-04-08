import { Location } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../auth.service';
import { IUser, LoginInfo } from '../server-settings';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {

  constructor(
    private authService: AuthService, 
    private router: Router, 
    private location: Location
  ) { }

  loginInfo = new LoginInfo('', '');
  submitted: boolean = false;
  loginResult: 'successful' | 'failed' = 'failed';

  ngOnInit(): void {
    
  }

  logged_navigate: (user: IUser) => void = (user: IUser) => {
    if (user.userName) {
      this.loginResult = 'successful';
      this.router.navigate(['/home']);
    } else {
      this.loginResult = 'failed'; 
    }
  }

  login(loginInfo: LoginInfo): void {
    this.submitted = true;
    this.authService.logIn(loginInfo).subscribe(this.logged_navigate);
  }
}
