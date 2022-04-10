import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { AuthService } from '../auth.service';
import { ChannelsService } from '../channels.service';
import { ChannelDetail } from '../server-settings';

@Component({
  selector: 'app-single-channel',
  templateUrl: './single-channel.component.html',
  styleUrls: ['./single-channel.component.css']
})
export class SingleChannelComponent implements OnInit {

  constructor(
    public authService: AuthService, 
    private channelsService: ChannelsService, 
    private route: ActivatedRoute
  ) { }
  
  channelDetail = new ChannelDetail();
  channelId = this.route.snapshot.paramMap.get('channelId');
  activeTab: 'videos' | 'stats' | 'management' = 'videos';

  ngOnInit(): void {
    this.authService.checkLogin().subscribe();
    if (this.channelId) {
      this.channelsService.getChannelDetail(this.channelId).subscribe(
        (channelDetail) => {
          this.channelDetail = channelDetail;
        }
      );
    }
  }

}
