import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BrowserModule, Title } from '@angular/platform-browser';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { NgChartsModule } from 'ng2-charts';
import { TagifyModule } from 'ngx-tagify';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { ChannelMgnComponent } from './channel-mgn/channel-mgn.component';
import { ChannelStatsComponent } from './channel-stats/channel-stats.component';
import { ChannelsComponent } from './channels/channels.component';
import { HomeComponent } from './home/home.component';
import { LoginComponent } from './login/login.component';
import { NavbarComponent } from './navbar/navbar.component';
import { NumberArrayMinPipe } from './number-array-min.pipe';
import { SearchVideoComponent } from './search-video/search-video.component';
import { SettingsComponent } from './settings/settings.component';
import { SingleChannelComponent } from './single-channel/single-channel.component';
import { SingleVideoComponent } from './single-video/single-video.component';
import { VideoListComponent } from './video-list/video-list.component';
import { VideosComponent } from './videos/videos.component';


@NgModule({
  declarations: [
    AppComponent,
    NavbarComponent,
    LoginComponent,
    HomeComponent,
    ChannelsComponent,
    SingleChannelComponent,
    VideoListComponent,
    ChannelStatsComponent,
    ChannelMgnComponent,
    SingleVideoComponent,
    VideosComponent,
    SearchVideoComponent,
    SettingsComponent,
    NumberArrayMinPipe
  ],
  imports: [
    BrowserModule,
    AppRoutingModule, 
    HttpClientModule, 
    FormsModule, 
    NgbModule, 
    NgChartsModule, 
    TagifyModule.forRoot()
  ],
  providers: [Title],
  bootstrap: [AppComponent]
})
export class AppModule { }
