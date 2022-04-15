import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';
import { TagData, TagifySettings } from 'ngx-tagify';
import { Observable, Subject } from 'rxjs';
import {
  debounceTime, distinctUntilChanged, switchMap
} from 'rxjs/operators';
import { ParseFuncsService } from '../parse-funcs.service';
import { SearchService } from '../search.service';
import { ISearchParams } from '../server-settings';
import { VideosService } from '../videos.service';


@Component({
  selector: 'app-search-video',
  templateUrl: './search-video.component.html',
  styleUrls: ['./search-video.component.css']
})
export class SearchVideoComponent implements OnInit {

  @Output() requestReload = new EventEmitter();

  constructor(
    private videosService: VideosService, 
    private parseFuncs: ParseFuncsService, 
    private router: Router, 
    private searchService: SearchService, 
    private route: ActivatedRoute
  ) { }

  searchPage: boolean = false;
  searchSum: string = '';
  searchAreaToggle: boolean = false;
  
  // date
  startDate?: string;
  endDate?: string;

  // talent tags
  talentTags: TagData[] = [];
  talentList: string[] = [];
  talentTagSettings: TagifySettings = {
    callbacks: {
      input: (e) => {this.talentSuggestionTerm.next(e.detail.value);}
    }, 
    placeholder: 'Talents'
  };
  talentSuggestionTerm = new Subject<string>();
  talentWhitelist$: Observable<TagData[]> = this.talentSuggestionTerm.pipe(
    debounceTime(100), 
    switchMap((talentInputStr: string) => this.videosService.getTagSuggestion("talents", talentInputStr))
  );

  // stream type tags
  streamTypeTags: TagData[] = [];
  streamTypeList: string[] = []
  streamTypeTagSettings: TagifySettings = {
    callbacks: {
      input: (e) => {this.streamTypeSuggestionTerm.next(e.detail.value);}
    }, 
    placeholder: 'Stream types'
  };
  streamTypeSuggestionTerm = new Subject<string>();
  streamTypeWhitelist$: Observable<TagData[]> = this.streamTypeSuggestionTerm.pipe(
    debounceTime(100), 
    distinctUntilChanged(), 
    switchMap((streamTypeInputStr: string) => this.videosService.getTagSuggestion("tags", streamTypeInputStr))
  );

  
  // title
  searchKeys: string = '';
  
  
  // sequencing
  timeDescending: boolean = false;


  // on search
  onSearch(timeDescending: boolean=false): void {
    const startDate = this.startDate ? this.parseFuncs.toIsoDateTimeUTC(this.startDate) : '';
    const endDate = this.endDate ? this.parseFuncs.toIsoDateTimeUTC(this.endDate) : '';
    this.talentList = this.parseFuncs.tagDataListToList(this.talentTags)
    this.streamTypeList = this.parseFuncs.tagDataListToList(this.streamTypeTags)
    const queryTalent = this.talentList.join(';');
    const queryType = this.streamTypeList.join(';');
    if (startDate || endDate || queryTalent || queryType || this.searchKeys) {
      const queryObj = this.searchService.paramsToQueryObj(startDate, endDate, this.talentTags, this.streamTypeTags, this.searchKeys, 10, timeDescending)
      this.router.navigate(['/search'], {queryParams: queryObj});
      this.requestReload.emit()
      this.checkSearchPage();
      this.searchAreaToggle = false;
    } 
  }

  ngOnInit(): void {
    this.checkSearchPage();
  }

  checkSearchPage(): void {
    const searchReg = /search*/;
    this.searchPage = searchReg.test(this.router.url.split('/')[1]);
    if (this.searchPage) {
      this.route.queryParamMap.subscribe(
        (paraMap: ParamMap) => {
          let searchSum = 'Showing result ';
          const queryObj: ISearchParams = this.searchService.urlToQueryObj(paraMap);
          const dateRange: string[] = queryObj.timeRange.split(';'); 
          let startDate: string = '';
          if (this.parseFuncs.isoDateToUnixStamp(dateRange[0]) !== 0) {
            startDate = this.parseFuncs.formatIsoDate(dateRange[0], 'YYYY-MM-DD');
            searchSum += `from ${startDate} `;
            this.startDate = startDate;
          } else {
            this.startDate = undefined;
          }
          let endDate: string = '';
          if (this.parseFuncs.getIsoToday() !== dateRange[1]) {
            endDate = this.parseFuncs.formatIsoDate(dateRange[1], 'YYYY-MM-DD');
            searchSum += `to ${endDate} `;
            this.endDate = endDate;
          } else {
            this.endDate = undefined;
          }
          let talentList: string[] = [];
          if (queryObj.talents) {
            let _talentList: string[] = queryObj.talents.split(';');
            talentList = _talentList.filter((s: string)=>(s!==''));
            this.talentTags = this.parseFuncs.listToTagDataList(talentList);
          } else{
            this.talentTags = [];
          }
          let streamTypeList: string[] = [];
          if (queryObj.tags) {
            let _streamTypeList: string[] = queryObj.tags.split(';');
            streamTypeList = _streamTypeList.filter((s: string)=>(s!==''));
            this.streamTypeTags = this.parseFuncs.listToTagDataList(streamTypeList);
          } else {
            this.streamTypeTags = [];
          }
          if (talentList.concat(streamTypeList).length>0) {
            searchSum += `on ${talentList.concat(streamTypeList).join(', ')}`;
          }
          if (queryObj.searchKeys) {
            this.searchKeys = queryObj.searchKeys;
          }
          if (searchSum !== 'Showing result ') {
            this.searchSum = searchSum;
          }
        }
      );
    }
  }
}
