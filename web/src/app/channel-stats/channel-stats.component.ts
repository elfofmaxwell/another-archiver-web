import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ChartConfiguration, ChartData } from 'chart.js';
import { ChannelsService } from '../channels.service';
import { ParseFuncsService } from '../parse-funcs.service';
import { ChannelStats } from '../server-settings';

@Component({
  selector: 'app-channel-stats',
  templateUrl: './channel-stats.component.html',
  styleUrls: ['./channel-stats.component.css']
})
export class ChannelStatsComponent implements OnInit {

  constructor(
    private channelsService: ChannelsService, 
    private route: ActivatedRoute, 
    private parseFuncs: ParseFuncsService
  ) {  }

  ngOnInit(): void {
    this.getChannelStats();
  }

  channelId = this.route.snapshot.paramMap.get('channelId');

  // update chart
  private _channelStats: ChannelStats = new ChannelStats();
  set channelStats(value: ChannelStats) {
    this._channelStats = value;
    // update collaboration chart
    this.collaborationColor = this.generateDoughnutColor(value.talentStats.talentName.length);
    let _tmpCollaborationData = this.collaborationData;
    _tmpCollaborationData.labels = value.talentStats.talentName.slice();
    _tmpCollaborationData.datasets[0].data = value.talentStats.num.slice();
    _tmpCollaborationData.datasets[0].backgroundColor = this.collaborationColor;
    _tmpCollaborationData.datasets[0].hoverBackgroundColor = this.collaborationColor;
    this.collaborationData = {
      labels: _tmpCollaborationData.labels, 
      datasets: _tmpCollaborationData.datasets
    };
    this.collaborationLabelToggle = [];
    for (let talentName of value.talentStats.talentName) {
      this.collaborationLabelToggle.push(true);
    }

    // update stream type chart
    this.streamTypeColor = this.generateDoughnutColor(value.tagStats.streamType.length);
    let _tmpStreamTypeData = this.streamTypeData;
    _tmpStreamTypeData.labels = value.tagStats.streamType.slice();
    _tmpStreamTypeData.datasets[0].data = value.tagStats.num.slice();
    _tmpStreamTypeData.datasets[0].backgroundColor = this.streamTypeColor;
    _tmpStreamTypeData.datasets[0].hoverBackgroundColor = this.streamTypeColor;
    this.streamTypeData = {
      labels: _tmpStreamTypeData.labels, 
      datasets: _tmpStreamTypeData.datasets
    }
    this.streamTypeLabelToggle = [];
    for (let streamType of value.tagStats.streamType) {
      this.streamTypeLabelToggle.push(true);
    }

    // update num/week chart
    let _tmpNumWeekData = this.numWeekData;
    _tmpNumWeekData.labels = value.videoNumStats.week;
    _tmpNumWeekData.datasets[0].data = value.videoNumStats.num;
    this.numWeekData = {
      labels: _tmpNumWeekData.labels,
      datasets: _tmpNumWeekData.datasets
    }

    // update length/week chart
    let _tmpLengthWeekData = this.lengthWeekData;
    _tmpLengthWeekData.labels = value.durationStats.week;
    _tmpLengthWeekData.datasets[0].data = value.durationStats.duration;
    this.lengthWeekData = {
      labels: _tmpLengthWeekData.labels,
      datasets: _tmpLengthWeekData.datasets
    }

    // update duration distr chart
    let _tmpDurationData = this.durationData;
    _tmpDurationData.labels = value.durationDistr.duration;
    _tmpDurationData.datasets[0].data = value.durationDistr.num;
    this.durationData = {
      labels: _tmpDurationData.labels,
      datasets: _tmpDurationData.datasets
    }
  }
  get channelStats(): ChannelStats {
    return this._channelStats;
  }

  // get channel stats data
  getChannelStats(timeDelta: number=0, lowerDateStamp: string='', upperDateStamp: string=''): void {
    if (this.channelId) {
      this.channelsService.getChannelStats(this.channelId, timeDelta, lowerDateStamp, upperDateStamp)
      .subscribe(
        (channelStats: ChannelStats): void => {
          this.channelStats = channelStats;
        }
      );
    }
  }

  // doughnut chart general settings
  generateDoughnutColor (dataLength: number): string[] {
    const color_list = []; 
    for (let i=0; i<dataLength; i++) {
        color_list.push('hsl('+String(i*360/(dataLength+1))+',80%,70%');
    }
    return color_list;
  }
  doughnutBorderColor: string = 'rgb(220, 220, 220)';
  doughnutHoverOffset: number = 6;

  doughnutOptions: ChartConfiguration['options'] = {
    responsive: true, 
    plugins: {
      legend: {
        display: false,
      },
    },
  }

  // line chart general settings
  lineOptions: ChartConfiguration['options'] = {
    responsive: true,
    scales: {
      x: {
        ticks: {
          autoSkip: true, 
          maxTicksLimit: 20
        }, 
      }, 
      y: {
        ticks: {
          maxTicksLimit: 8, 
        },
        beginAtZero: true,
      },
    }, 
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  // bar chart general settings
  barOptions: ChartConfiguration['options'] = {
    responsive: true, 
    plugins: {
      legend: {
        display: false,
      },
    }
  }


  // stats filter settings
  activeFilter: 0 | 30 | 90 | 365 | -1 = 0;
  advFilter: boolean = false;
  lessThanWeek: boolean= false;
  today: string = this.parseFuncs.getToday('YYYY-MM-DD');
  _filterStartDate: string= '';
  _filterEndDate: string = '';
  set filterStartDate(startDate: string) {
    this._filterStartDate = this.parseFuncs.toIsoDateTimeUTC(startDate);
    this.lessThanWeek = (this.parseFuncs.calculateDateDiff(this._filterEndDate, this._filterStartDate) <= 7);
  }
  get filterStartDate(): string {
    return this.parseFuncs.formatIsoDate(this._filterStartDate, 'YYYY-MM-DD');
  }
  set filterEndDate(endDate: string) {
    this._filterEndDate = this.parseFuncs.toIsoDateTimeUTC(endDate);
    this.lessThanWeek = (this.parseFuncs.calculateDateDiff(this._filterEndDate, this._filterStartDate) <= 7);
  }
  get filterEndDate(): string {
    return this.parseFuncs.formatIsoDate(this._filterEndDate, 'YYYY-MM-DD');
  }



  // collaborations
  collaborationData: ChartData<'doughnut'> = {
    labels: [],
    datasets: [{data: [], hoverBorderColor: 'rgb(220, 220, 220)', hoverOffset: 6}],
  }
  collaborationColor: string[] = [];
  collaborationLabelToggle: boolean[] = [];

  toggleTalentLabel (i: number) {
    if (this.collaborationLabelToggle[i]) {
      this.collaborationLabelToggle[i] = false;
      let _tmpData = this.collaborationData;
      _tmpData.datasets[0].data[i] = 0;
      this.collaborationData = {
        labels: _tmpData.labels, 
        datasets: _tmpData.datasets
      };
    } else {
      this.collaborationLabelToggle[i] = true;
      let _tmpData = this.collaborationData;
      _tmpData.datasets[0].data[i] = this.channelStats.talentStats.num[i];
      this.collaborationData = {
        labels: _tmpData.labels, 
        datasets: _tmpData.datasets
      };
    }
  }


  // stream types
  streamTypeData: ChartData<'doughnut'> = {
    labels: [],
    datasets: [{data: [], hoverBorderColor: 'rgb(220, 220, 220)', hoverOffset: 6},],
  }
  streamTypeColor: string[] = [];
  streamTypeLabelToggle: boolean[] = [];

  toggleStreamTypeLabel (i: number) {
    if (this.streamTypeLabelToggle[i]) {
      this.streamTypeLabelToggle[i] = false;
      let _tmpData = this.streamTypeData;
      _tmpData.datasets[0].data[i] = 0;
      this.streamTypeData = {
        labels: _tmpData.labels, 
        datasets: _tmpData.datasets
      };
    } else {
      this.streamTypeLabelToggle[i] = true;
      let _tmpData = this.streamTypeData;
      _tmpData.datasets[0].data[i] = this.channelStats.tagStats.num[i];
      this.streamTypeData = {
        labels: _tmpData.labels, 
        datasets: _tmpData.datasets
      };
    }
  }

  // video num/week
  numWeekData: ChartData<'line'> = {
    labels: [], 
    datasets: [{
      data: [], 
      borderColor: 'rgb(255, 191, 191)', 
      pointBackgroundColor: 'rgb(255, 163, 163)',
      pointBorderColor: 'rgb(255, 163, 163)',
      pointHoverBackgroundColor: 'rgb(255, 153, 153)', 
      pointHoverBorderColor: 'rgb(255, 153, 153)', 
      tension: 0.5,
    }]
  }

  // video length/week
  lengthWeekData: ChartData<'line'> = {
    labels: [], 
    datasets: [{
      data: [], 
      borderColor: 'rgb(179, 221, 242)', 
      pointBackgroundColor: 'rgb(142, 200, 230)',
      pointBorderColor: 'rgb(142, 200, 230)',
      pointHoverBackgroundColor: 'rgb(132, 190, 230)', 
      pointHoverBorderColor: 'rgb(132, 190, 230)', 
      tension: 0.5,
    }]
  }

  // video length duration
  durationData: ChartData<'bar'> = {
    labels: [], 
    datasets: [{
      data: [],
      backgroundColor: "rgb(203, 237, 183)", 
      hoverBackgroundColor: "rgb(193, 237, 173)",
    }]
  }
}
