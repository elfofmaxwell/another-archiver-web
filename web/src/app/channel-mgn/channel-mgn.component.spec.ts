import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ChannelMgnComponent } from './channel-mgn.component';

describe('ChannelMgnComponent', () => {
  let component: ChannelMgnComponent;
  let fixture: ComponentFixture<ChannelMgnComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ChannelMgnComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ChannelMgnComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
