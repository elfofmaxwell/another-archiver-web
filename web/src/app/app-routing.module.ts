import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ChannelsComponent } from './channels/channels.component';
import { HomeComponent } from './home/home.component';
import { LoginComponent } from './login/login.component';
import { SingleChannelComponent } from './single-channel/single-channel.component';
import { SingleVideoComponent } from './single-video/single-video.component';

const routes: Routes = [
  {path: 'login', component: LoginComponent}, 
  {path: 'home', component: HomeComponent}, 
  {path: 'channels', component: ChannelsComponent},
  {path: 'channel/:channelId', component: SingleChannelComponent},
  {path: '', redirectTo: 'home', pathMatch: 'full'}, 
  {path: 'video/:videoId', component: SingleVideoComponent}, 
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
