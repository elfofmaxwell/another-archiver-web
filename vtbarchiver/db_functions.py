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


def full_text_search(table_name: str, column_name: str, search_key: str) -> list: 
    '''
    Search with match method, return list of video_id
    '''
    db = get_db()
    cur = db.cursor()
    try: 
        cur.execute('SELECT video_id FROM ? WHERE ? MATCH "?" ORDER BY rank', (table_name, column_name, search_key))
        searched_results = [i['video_id'] for i in cur.fetchall()]
        return searched_results
    finally: 
        cur.close()


def find_common_items(*lists_for_reduction): 
    def find_common_2(list1, list2): 
        return list(set(list1).intersection(list2))
    return reduce(find_common_2, lists_for_reduction)


def find_tags(table_name: str, column_name: str, tag_list: list) -> list:
    '''
    tag list: list of strings of tags to be find in column_name of table_name
    '''
    db = get_db()
    cur = db.cursor()
    result_list_set = []
    try: 
        for tag in tag_list: 
            cur.execute("SELECT video_id FROM ? WHERE ?=?", (table_name, column_name, tag))
            result_list = [i['video_id'] for i in cur.fetchall()]
            result_list_set.append(result_list)
        reduced_result_list = find_common_items(*result_list_set)
        return reduced_result_list
    finally:
        cur.close()



