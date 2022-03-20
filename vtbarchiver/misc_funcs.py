# -*- coding: utf-8 -*-

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
