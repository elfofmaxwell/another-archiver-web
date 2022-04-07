import { Component, OnInit } from '@angular/core';
import { AuthService } from '../auth.service';
import { IUser } from '../server-settings';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.css']
})
export class NavbarComponent implements OnInit {

  isMenuCollapsed: boolean = true; 
  userInfo: IUser = {userId: -1, userName: ''}

  constructor(
    private authService: AuthService
  ) { }

  ngOnInit(): void {
    this.checkLogin();
  }

  toggle_navbar (): void {
    this.isMenuCollapsed = !this.isMenuCollapsed;
  }

  checkLogin (): void {
    this.authService.checkLogin().subscribe(userInfo => this.userInfo = userInfo);
  }
}
