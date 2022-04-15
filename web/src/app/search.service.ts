import { HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { ParamMap } from '@angular/router';
import { TagData } from 'ngx-tagify';
import { ParseFuncsService } from './parse-funcs.service';
import { IQueryObj, ISearchParams } from './server-settings';

@Injectable({
  providedIn: 'root'
})
export class SearchService {

  constructor(
    private parseFuncs: ParseFuncsService
  ) { }
  

  paramsToQueryObj (
    startDate: string = '', 
    endDate: string = '', 
    talentTags: TagData[] = [], 
    streamTypeTags: TagData[] = [], 
    searchKeys: string = '', 
    pageSize: number = 10, 
    timeDescending: boolean = false
    ) {
      if (!startDate) {
        startDate = this.parseFuncs.getUnixZeroIso();
      }
      if (!endDate) {
        endDate = this.parseFuncs.getIsoTomorrow();
      }
      const queryDate = `${startDate};${endDate}`;
      const queryTalent = this.parseFuncs.tagDataListToList(talentTags).join(';');
      const queryType = this.parseFuncs.tagDataListToList(streamTypeTags).join(';');
      const queryObj = {
        timeRange: queryDate, 
        tags: queryType, 
        talents: queryTalent, 
        searchKeys: searchKeys, 
        timeDescending: timeDescending,
        pageSize: pageSize, 
      };
      return queryObj;
    }

  
  objToBackendQueryString (queryObj: IQueryObj): HttpParams {
    const queryStr = new HttpParams(
      {
        fromObject: queryObj
      }
    ); 
    return queryStr
  }

  urlToQueryObj(urlSnapshot: ParamMap): ISearchParams {
    const queryObj: ISearchParams = {
      timeRange: urlSnapshot.get('timeRange') || '', 
      tags: urlSnapshot.get('tags') || '', 
      talents: urlSnapshot.get('talents') || '', 
      searchKeys: urlSnapshot.get('searchKeys') || '', 
      timeDescending: urlSnapshot.get('timeDescending')==='true' ? true : false, 
      pageSize: Number(urlSnapshot.get('pageSize')) || 10, 
    }
    return queryObj;
  }
}
