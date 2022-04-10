import { Injectable } from '@angular/core';
import * as moment from 'moment';


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

  getToday(format: string='MMM DD, YYYY'): string {
    return moment().format(format);
  }
}
