# -*- coding: utf-8 -*-

import sqlite3

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

