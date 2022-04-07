export const SERVERURL = 'http://127.0.0.1:4201';
export const INITIAL_URL = '/home';

export class LoginInfo {
    userName: string;
    password: string;

    constructor (userName: string, password: string) {
        this.userName = userName;
        this.password = password;
    }
}

export interface IUser {
    userId: number;
    userName: string;
}
