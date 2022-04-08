import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ChannelsComponent } from './channels/channels.component';
import { HomeComponent } from './home/home.component';
import { LoginComponent } from './login/login.component';

const routes: Routes = [
  {path: 'login', component: LoginComponent}, 
  {path: 'home', component: HomeComponent}, 
  {path: 'channels', component: ChannelsComponent},
];

@NgModule({
  declarations: [],
  imports: [
    RouterModule.forRoot(routes), 
  ], 
  exports: [
    RouterModule, 
  ], 
})
export class AppRoutingModule { }
