import { TestBed } from '@angular/core/testing';

import { AppGaurdService } from './app-gaurd.service';

describe('AppGaurdService', () => {
  let service: AppGaurdService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AppGaurdService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
