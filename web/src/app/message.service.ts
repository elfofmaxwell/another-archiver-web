import { Injectable } from '@angular/core';

export interface IMessage {
  message: string;
  messageType: 'warning' | 'danger' | 'success' | 'info';
}

@Injectable({
  providedIn: 'root'
})
export class MessageService {

  constructor() { }

  pushMessage (messageList: IMessage[], message: string, messageType: IMessage['messageType']) {
    messageList.push({message: message, messageType: messageType});
  }
  
  clearMessage (messageList: IMessage[]) {
    while (messageList.length) {
      messageList.pop();
    }
  }

  setSingleMessage (messageList: IMessage[], message: string, messageType: IMessage['messageType']) {
    this.clearMessage(messageList); 
    this.pushMessage(messageList, message, messageType);
  }
  
}
