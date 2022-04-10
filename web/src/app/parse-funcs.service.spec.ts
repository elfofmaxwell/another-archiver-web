import { TestBed } from '@angular/core/testing';

import { ParseFuncsService } from './parse-funcs.service';

describe('ParseFuncsService', () => {
  let service: ParseFuncsService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ParseFuncsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
