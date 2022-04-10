import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ChannelStatsComponent } from './channel-stats.component';

describe('ChannelStatsComponent', () => {
  let component: ChannelStatsComponent;
  let fixture: ComponentFixture<ChannelStatsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ChannelStatsComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ChannelStatsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
