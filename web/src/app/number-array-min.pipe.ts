import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'numberArrayMin'
})
export class NumberArrayMinPipe implements PipeTransform {

  transform(numberArray: number[]): number {
    return Math.min(...numberArray);
  }

}
