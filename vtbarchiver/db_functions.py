# -*- coding: utf-8 -*-

import sqlite3
from functools import reduce

import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db(): 
    # get a db connection for each request (each g) at set path for the database
    if 'db' not in g: 
        g.db = sqlite3.connect(
            current_app.config['DATABASE'], 
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    # close db if there is a db in current request  
    db = g.pop('db', None)
    if db is not None: 
        db.close()

def init_db(): 
    db = get_db()
    cur = db.cursor()
    with current_app.open_resource('init_db.sql') as f: 
        cur.executescript(f.read().decode('utf8'))
    cur.close()
    db.commit()

@click.command('init-db')
@with_appcontext
def init_db_command(): 
    '''
    Clear current db (if exists) and create a new one
    '''
    init_db()
    click.echo('Database created/reinitialized')


def full_text_search(table_name: str, search_key: str) -> list: 
    '''
    Search with match method, return list of video_id
    '''
    db = get_db()
    cur = db.cursor()
    try: 
        cur.execute('SELECT video_id FROM %s WHERE %s MATCH ? ORDER BY rank' % (table_name, table_name), (search_key, ))
        searched_results = [i['video_id'] for i in cur.fetchall()]
        return searched_results
    finally: 
        cur.close()


def time_range_filter(start_time, end_time): 
    '''
    time in UTC ISO 8601 format YYYY-MM-DDTHH-MM-SSZ
    '''
    db = get_db()
    cur = db.cursor()
    try: 
        cur.execute('SELECT video_id FROM video_list WHERE upload_date>? AND upload_date<?', (start_time, end_time))
        searched_results = [i['video_id'] for i in cur.fetchall()]
        return searched_results
    finally: 
        cur.close()


def find_common_items(*lists_for_reduction): 
    def find_common_2(list1, list2): 
        return list(set(list1).intersection(list2))
    if len(lists_for_reduction) > 1: 
        return reduce(find_common_2, lists_for_reduction)
    elif len(lists_for_reduction) == 1: 
        return lists_for_reduction[0]
    else: 
        return []


def find_tags(table_name: str, column_name: str, tag_list: list) -> list:
    '''
    tag list: list of strings of tags to be find in column_name of table_name
    '''
    db = get_db()
    cur = db.cursor()
    result_list_set = []
    try: 
        for tag in tag_list: 
            cur.execute("SELECT video_id FROM %s WHERE %s=? COLLATE NOCASE" % (table_name, column_name), (tag, ))
            result_list = [i['video_id'] for i in cur.fetchall()]
            result_list_set.append(result_list)
        reduced_result_list = find_common_items(*result_list_set)
        return reduced_result_list
    finally:
        cur.close()


def tag_suggestions(tag_type: str, query_str: str): 
    table_name = ''
    column_name = ''
    suggestion_list = []
    db = get_db()
    cur = db.cursor()
    try: 
        if tag_type == 'talents': 
            cur.execute('SELECT talent_name FROM talent_participation WHERE talent_name LIKE ? GROUP BY talent_name', ('%'+query_str+'%', ))
            suggestion_list = [i['talent_name'] for i in cur.fetchall()]
        elif tag_type == 'tags': 
            cur.execute('SELECT stream_type FROM stream_type WHERE stream_type LIKE ? GROUP BY stream_type', ('%'+query_str+'%', ))
            suggestion_list = [i['stream_type'] for i in cur.fetchall()] 
        return suggestion_list
    finally: 
        cur.close()