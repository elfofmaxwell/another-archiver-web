import { TestBed } from '@angular/core/testing';
import { AppGuardService } from './app-gaurd.service';


describe('AppGaurdService', () => {
  let service: AppGuardService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AppGuardService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
