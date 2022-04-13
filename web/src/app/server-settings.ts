export const SERVERURL = 'http://127.0.0.1:4201';
export const INITIAL_URL = '/home';

export class LoginInfo {
  userName: string;
  password: string;

  constructor (userName: string, password: string) {
    this.userName = userName;
    this.password = password;
  }
}

export interface IUser {
  userId: number;
  userName: string;
}

export class ChannelOverview {
  channelId: string; 
  channelName: string;
  thumbUrl: string;

  constructor (channelId: string = '', channelName: string = '', thumbUrl: string = '') {
    this.channelId = channelId; 
    this.channelName = channelName; 
    this.thumbUrl = thumbUrl;
  }
}

export class ChannelDetail extends ChannelOverview {

  talentName: string;
  videoNum: number;
  checkpointIndex: number;

  constructor (channelId: string = '', channelName: string = '', thumbUrl: string = '', talentName: string = '', videoNum: number = 0, checkpointIndex: number = 0) {
    super(channelId, channelName, thumbUrl); 
    this.talentName = talentName;
    this.videoNum = videoNum; 
    this.checkpointIndex = checkpointIndex;
  }
}

export class VideoOverview {
  videoId: string;
  title: string;
  uploadDate: string; 
  duration: string;
  uploadIndex: number; 
  thumbUrl: string;
  localPath: string;

  constructor (videoId: string='', title: string='', uploadDate: string='', duration: string='', uploadIndex: number=0, thumbUrl: string='', localPath: string='') {
    this.videoId = videoId;
    this.title = title;
    this.uploadDate = uploadDate;
    this.duration = duration;
    this.uploadIndex = uploadIndex; 
    this.thumbUrl = thumbUrl;
    this.localPath = localPath;
  }
}

export class VideoDetail extends VideoOverview {
  channelId: string;
  channelName: string;
  talentNames: string[];
  streamTypes: string[];

  constructor (
    videoId: string='', 
    title: string='', 
    uploadDate: string='', 
    duration: string='', 
    uploadIndex: number=0, 
    thumbUrl: string='', 
    localPath: string='', 
    channelId: string='', 
    channelName: string='', 
    talentNames: string[]=[], 
    streamTypes: string[]=[]
    ) {
      super(videoId, title, uploadDate, duration, uploadIndex, thumbUrl, localPath);
      this.channelId = channelId; 
      this.channelName = channelName;
      this.talentNames = talentNames;
      this.streamTypes = streamTypes;
    }
}

export class AddedVideoDetail extends VideoDetail {
  serverMessage?: string;
  constructor (
    title: string='', 
    uploadDate: string='', 
    duration: string='', 
    uploadIndex: number=0, 
    thumbUrl: string='', 
    localPath: string='', 
    videoId: string='', 
    channelId: string='', 
    channelName: string='', 
    talentNames: string[]=[], 
    streamTypes: string[]=[]
    ) {
      super(videoId, title, uploadDate, duration, uploadIndex, thumbUrl, localPath, channelId, channelName, talentNames, streamTypes);
    }
}

export interface IVideoList {
  videoNum: number;
  videoList: VideoOverview[];
}

// stats types
class collaborationData {
  talentName: string[] = [];
  num: number[] = [];
}
class streamTypeData {
  streamType: string[] = [];
  num: number[] = [];
}
class videoNumData {
  week: string[] = [];
  num: number[] = [];
}
class DurationStatsData {
  week: string[] = [];
  duration: number[] = [];
}
class DurationDistrData {
 duration: string[] = [];
 num: number[] = [];
}
export class ChannelStats {
  talentStats: collaborationData;
  tagStats: streamTypeData;
  durationStats: DurationStatsData;
  durationDistr: DurationDistrData;
  videoNumStats: videoNumData;

  constructor() {
    this.talentStats = {talentName: [], num: []};
    this.tagStats = {streamType: [], num: []};
    this.durationStats = {week: [], duration: []};
    this.durationDistr = {duration:[], num:[]};
    this.videoNumStats = {week:[], num:[]};
  }
}

export class ErrorMessage {
  status: number=418;
  statusText: string="I'm a teapot";
  message: string="I'm a teapot";
}

export interface IDownloading {
  downloading: boolean;
}