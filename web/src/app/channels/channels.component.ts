import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../auth.service';
import { ChannelsService } from '../channels.service';
import { ChannelOverview } from '../server-settings';

@Component({
  selector: 'app-channels',
  templateUrl: './channels.component.html',
  styleUrls: ['./channels.component.css']
})
export class ChannelsComponent implements OnInit {

  constructor(
    private channelsService: ChannelsService, 
    private router: Router, 
    public authService: AuthService
  ) { }

  channelList: ChannelOverview[] = [];
  addChannelField: boolean = false;
  newChannelId: string = '';
  submittedNewChannel: boolean = false;
  addChannelResult: boolean = false;
  fetchChannelResult: boolean = false;
  fetchFailedChannels: ChannelOverview[] = [];
  fetchFailedChannelIds: string = '';


  ngOnInit(): void {
    this.getChannels();
    this.authService.checkLogin().subscribe();
  }

  getChannels(): void {
    this.channelsService.getChannelList().subscribe(
      (channelList) => {
        this.channelList = channelList;
      }
    );
  }

  goToChannel(channelId: string): void {
    this.router.navigate(['/channel', channelId], {queryParams: {page: 1}});
  }

  toggleAddChannel(): void {
    this.addChannelField = true;
  }
  
  addNewChannel(newChannelId: string): void {
    this.submittedNewChannel = true;
    this.addChannelResult = true;
    this.channelsService.addYouTubeChannel(newChannelId).subscribe(
      (newChannel: ChannelOverview) => {
        if (newChannel.channelId) {
          this.newChannelId = '';
          this.addChannelResult = true;
          this.getChannels();
          this.addChannelField = false;
        } else {
          this.addChannelResult = false;
        }
      }
    );
  }

  fetchAllChannels(): void {
    this.channelsService.fetchAllChannel().subscribe(
      (fetchedChannelList: ChannelOverview[]) => {
        if (fetchedChannelList.length === this.channelList.length) {
          this.fetchFailedChannels = [];
          this.fetchChannelResult = true;
        } else {
          const fetchedChannelIds = fetchedChannelList.map(
            (fetchedChannel: ChannelOverview): string => {
              return fetchedChannel.channelId;
            }
          );
          this.fetchFailedChannels = this.channelList.filter(
            (channel: ChannelOverview): boolean => {
              return (fetchedChannelIds.indexOf(channel.channelId) >= 0);
            }
          );
          this.fetchFailedChannelIds = this.fetchFailedChannels.map((c: ChannelOverview): string => {return c.channelName}).join(', ');
        }
      }
    );
  }
}
