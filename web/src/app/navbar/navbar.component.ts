import { Component, OnInit } from '@angular/core';
import { AuthService } from '../auth.service';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.css']
})
export class NavbarComponent implements OnInit {

  isMenuCollapsed: boolean = true; 

  constructor(
    public authService: AuthService
  ) { }

  ngOnInit(): void {
    this.checkLogin();
  }

  toggle_navbar (): void {
    this.isMenuCollapsed = !this.isMenuCollapsed;
  }

  checkLogin (): void {
    this.authService.checkLogin().subscribe();
  }

  logOut (): void {
    this.authService.logOut().subscribe(); 
  }
}
