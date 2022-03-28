# -*- coding: utf-8 -*-
import datetime

import isodate


def get_pagination(current_page, page_num, pagination_length): 
    if pagination_length > page_num: 
        pagination_list = list(range(1, page_num+1))
        return pagination_list
    tmp_pagination_list = list(range(current_page - (pagination_length-1)//2, current_page - (pagination_length-1)//2 + pagination_length))
    pagination_list = tmp_pagination_list[:]
    if tmp_pagination_list[0] < 1: 
        pagination_list = [i + 1 - tmp_pagination_list[0] for i in tmp_pagination_list]
    elif tmp_pagination_list[-1] > page_num: 
        pagination_list = [i - (tmp_pagination_list[-1]-page_num) for i in tmp_pagination_list]
    return pagination_list


class Pagination(): 
    def __init__(self, current_page, page_num, pagination_length) -> None:
        self.list = get_pagination(current_page, page_num, pagination_length)
        self.active_page = current_page
        self.links = []
        self.first_link = ''
        self.last_link = ''


def to_isoformat(date_obj): 
    return datetime.datetime.isoformat(date_obj, timespec="seconds")+'Z'


def calculate_date_from_delta(delta_days: int): 
    '''
    calculate the date since which delta_time days have passed
    delta_time: days since now
    '''
    return to_isoformat(datetime.datetime.utcnow() - datetime.timedelta(days=delta_days))+'Z'


def calculate_date_week(delta_week: int): 
    return to_isoformat(datetime.datetime.utcnow() - datetime.timedelta(days=delta_week))+'Z'


def week_stops(start_date_str, end_date_str): 
    '''
    input: ISO 8601 date, return list from date earlier than that day to today with step size of 1 week, from earlist to latest
    '''
    end_date_obj = datetime.datetime.fromisoformat(end_date_str[:-1])
    week_stop_list = [end_date_obj]
    current_stop = week_stop_list[0]
    while current_stop > datetime.datetime.fromisoformat(start_date_str[:-1]): 
        current_stop = current_stop - datetime.timedelta(weeks=1)
        week_stop_list.append(current_stop)
    week_stop_list.reverse()
    return list(map(to_isoformat, week_stop_list))


def parse_duration(duration_str_pt): 
    return isodate.parse_duration(duration_str_pt).seconds
