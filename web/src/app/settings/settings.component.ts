import { Component, OnInit } from '@angular/core';
import { DownloaderService } from '../downloader.service';
import { IMessage, MessageService } from '../message.service';
import { ErrorMessage, IDownloading, IScanned, Settings } from '../server-settings';
import { SettingsService } from '../settings.service';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})
export class SettingsComponent implements OnInit {

  constructor(
    private settingsService: SettingsService, 
    private messageService: MessageService, 
    private downloaderService: DownloaderService
  ) { }
  
  messageList: IMessage[] = [];
  settingObj: Settings = new Settings();
  downloaderStatus: boolean = true;

  ngOnInit(): void {
    this.getSettings(); 
    this.checkDownloader();
  }

  getSettings() {
    this.settingsService.getSettings()
    .subscribe(
      (settingResult: Settings|ErrorMessage) => {
        if (settingResult instanceof ErrorMessage) {
          this.messageService.setSingleMessage(this.messageList, settingResult.message, 'danger');
        } else {
          this.messageService.clearMessage(this.messageList);
          this.settingObj = settingResult;
        }
      }
    );
  }

  putSettings() {
    this.settingsService.putSettings(this.settingObj)
    .subscribe(
      (settingResult: Settings|ErrorMessage) => {
        if (settingResult instanceof ErrorMessage) {
          this.messageService.setSingleMessage(this.messageList, settingResult.message, 'danger');
        } else {
          this.messageService.clearMessage(this.messageList);
          this.settingObj = settingResult;
        }
      }
    )
  }

  checkDownloader() {
    this.downloaderService.checkDownloading()
    .subscribe(
      (checkResult: IDownloading|ErrorMessage) => {
        if (checkResult instanceof ErrorMessage) {
          this.messageService.setSingleMessage(this.messageList, checkResult.message, 'danger');
        } else {
          this.messageService.clearMessage(this.messageList);
          this.downloaderStatus = checkResult.downloading;
        }
      }
    );
  }


  onScanLocal() {
    this.settingsService.scanLocalFiles()
    .subscribe(
      (scanResult: IScanned|ErrorMessage) => {
        if (scanResult instanceof ErrorMessage) {
          this.messageService.setSingleMessage(this.messageList, scanResult.message, 'danger');
        } else {
          if (scanResult.scanned) {
            this.messageService.setSingleMessage(this.messageList, 'Local File Scanned', 'success');
          } else {
            this.messageService.setSingleMessage(this.messageList, 'Oops, scanning failed!', 'danger');
          }
        }
      }
    );
  }


  onTriggerDownload() {
    this.downloaderService.triggerDownload()
    .subscribe(
      (downloadResult: IDownloading|ErrorMessage) => {
        if (downloadResult instanceof ErrorMessage) {
          this.messageService.setSingleMessage(this.messageList, downloadResult.message, 'danger'); 
        } else {
          this.downloaderStatus = downloadResult.downloading;
          if (downloadResult.downloading) {
            this.messageService.setSingleMessage(this.messageList, 'Downloader started', 'success');
          } else {
            this.messageService.setSingleMessage(this.messageList, 'Downloader starting failed!', 'danger');
          }
        }
      }
    );
  }


  onTriggerFetchDownload() {
    this.downloaderService.triggerFetchDownload()
    .subscribe(
      (downloadResult: IDownloading|ErrorMessage) => {
        if (downloadResult instanceof ErrorMessage) {
          this.messageService.setSingleMessage(this.messageList, downloadResult.message, 'danger');
        } else {
          this.downloaderStatus = downloadResult.downloading;
          if (downloadResult.downloading) {
            this.messageService.setSingleMessage(this.messageList, 'Downloader started', 'success');
          } else {
            this.messageService.setSingleMessage(this.messageList, 'Downloader starting failed!', 'danger');
          }
        }
      }
    )
  }
  
  
  onStopDownloader() {
    this.downloaderService.stopDownload()
    .subscribe(
      (downloadResult: IDownloading|ErrorMessage) => {
        if (downloadResult instanceof ErrorMessage) {
          this.messageService.setSingleMessage(this.messageList, downloadResult.message, 'danger');
        } else {
          this.downloaderStatus = downloadResult.downloading;
          if (downloadResult.downloading) {
            this.messageService.setSingleMessage(this.messageList, 'Stopping downloader failed!', 'danger'); 
          } else {
            this.messageService.setSingleMessage(this.messageList, 'Downloader stopped', 'success');
          }
        }
      }
    );
  }
}
