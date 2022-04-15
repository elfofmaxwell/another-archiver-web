import { HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import * as moment from 'moment';
import { TagData } from 'ngx-tagify';
import { Observable, of } from 'rxjs';
import { ErrorMessage } from './server-settings';


@Injectable({
  providedIn: 'root'
})
export class ParseFuncsService {

  constructor() { }

  formatIsoDate(isoDate: string, format: string='MMM DD, YYYY'): string {
    const dateMomentObj = moment(isoDate);
    if (dateMomentObj.isValid()) {
      return dateMomentObj.format(format);
    } else {
      return '';
    }
  }

  formatIsoDuration(isoDuration: string): string {
    const durationMomentObj = moment.duration(isoDuration);
    if (moment.isDuration(durationMomentObj)) {
      let formattedIsoDuration = moment.utc(durationMomentObj.asMilliseconds()).format('HH:mm:ss');
      if (formattedIsoDuration.startsWith('00:')) {
        formattedIsoDuration = formattedIsoDuration.slice(3);
      }
      return formattedIsoDuration;
    } else {
      return '';
    }
  }

  toIsoDateTimeUTC(dateString: string): string {
    const dateMomentObj = moment(dateString);
    if (dateMomentObj.isValid()) {
      return dateMomentObj.utc().format();
    } else {
      return '';
    }
  }

  toIsoDuration(durationString: string): string {
    const durationObj = moment.duration(durationString);
    if (moment.isDuration(durationObj)) {
      return durationObj.toISOString();
    } else {
      return '';
    }
  }

  getToday(format: string='MMM DD, YYYY'): string {
    return moment().format(format);
  }

  getIsoToday(): string {
    return moment.utc().format();
  }

  getUnixZeroIso(): string {
    return moment.unix(0).utc().format();
  }

  isoDateToUnixStamp(isoDate: string): number {
    const dateMomentObj = moment(isoDate);
    if (dateMomentObj.isValid()) {
      return dateMomentObj.unix();
    } else {
      return 0;
    }
  }

  calculateDateDiff(isoStartDateTime: string, isoEndDateTime: string): number {
    const startDateObj = moment(isoStartDateTime); 
    const endDateObj = moment(isoEndDateTime);
    if (startDateObj.isValid() && endDateObj.isValid()) {
      return endDateObj.diff(startDateObj, 'days');
    } else {
      return 0;
    }
  }

  tagDataListToList(tagDataList: TagData[]): string[] {
    const dataList: string[] = [];
    for (let tagData of tagDataList) {
      dataList.push(tagData.value);
    }
    return dataList;
  }

  listToTagDataList(dataList: string[]): TagData[] {
    const tagDataList: TagData[] = [];
    for (let dataString of dataList) {
      tagDataList.push({value: dataString.trim()});
    }
    return tagDataList;
  }

  parseHttpError(httpError: HttpErrorResponse): Observable<ErrorMessage> {
      const errorMessage = new ErrorMessage();
      errorMessage.status = httpError.status;
      errorMessage.statusText = httpError.statusText;
      errorMessage.message = "Oops, something went wrong.";
      return of(errorMessage);
  }
}
