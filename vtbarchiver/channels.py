# -*- coding: utf-8 -*-

from math import ceil
from flask import (current_app, g, Blueprint, flash, redirect, render_template, request, url_for)

from vtbarchiver.channel_records import fetch_channel, update_checkpoint
from vtbarchiver.db_functions import get_db
from vtbarchiver.fetch_video_list import fetch_all, fetch_uploaded_list
from vtbarchiver.fetch_video_list import add_talent_name as add_name
from vtbarchiver.management import login_required


bp = Blueprint('channels', __name__, url_prefix='/channels')


# channels page
@bp.route('/')
def channels(): 
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT channel_id, channel_name, thumb_url FROM channel_list')
    channel_list = cur.fetchall()
    return render_template('channels/channel_list.html', channel_list=channel_list)


# add channel
@bp.route('/add-channel', methods=('GET', 'POST'))
@login_required
def add_channel(): 
    if request.method == "POST": 
        fetch_channel(request.form['channel_id'])
        fetch_uploaded_list(request.form['channel_id'])
    return redirect(url_for('channels.channels'))


# fetch_channel
@bp.route('/fetch-channels')
@login_required
def fetch_channels(): 
    fetch_all()
    return redirect(url_for('channels.channels'))


# single channel page
@bp.route('/<channel_id>/', defaults={'page': 1})
@bp.route('/<channel_id>/page/<int:page>')
def single_channel(channel_id, page): 
    db = get_db()
    try: 
        cur = db.cursor()
        cur.execute("SELECT * FROM channel_list WHERE channel_id = ?", (channel_id, ))
        channel_info = cur.fetchone()

        cur.execute("SELECT COUNT(*) video_num FROM video_list WHERE channel_id = ?", (channel_id, ))
        video_num = cur.fetchone()['video_num']
        page_entry_num = 5
        page_num = ceil(video_num/page_entry_num)
        cur.execute(
            '''
            SELECT vl.video_id video_id, vl.title title, vl.upload_date upload_date, vl.thumb_url thumb_url, vl.talents talents, lv.id local_id
            FROM video_list vl
            LEFT OUTER JOIN local_videos lv
            ON vl.video_id = lv.video_id
            WHERE vl.channel_id = ? 
            ORDER BY vl.upload_idx DESC
            LIMIT ? OFFSET ?
            ''', 
            (channel_id, page_entry_num, (page-1)*page_num)
        )
        videos_on_page = cur.fetchall()

        return render_template('channels/single_channel.html', channel_info=channel_info, page_num=page_num, videos_on_page=videos_on_page)
    finally: 
        cur.close()


# edit checkpoint
@bp.route('/<channel_id>/edit-checkpoint', methods=("POST", "GET"))
@login_required
def edit_checkpoint(channel_id): 
    if request.method == "POST": 
        error = ''
        update_checkpoint_result = update_checkpoint(channel_id, **request.form)
        if update_checkpoint_result != 1: 
            error = "Update failed. Please check your input. "
            flash(error)
            return redirect(url_for('channels.single_channel', channel_id=channel_id)+'#edit-checkpoint-dialog')
        return redirect(url_for('channels.single_channel', channel_id=channel_id))
    return redirect(url_for('channels.single_channel', channel_id=channel_id))


# edit talent name for a channel
@bp.route('/<channel_id>/edit-talent', methods=("POST", "GET"))
@login_required
def edit_talent(channel_id): 
    if request.method == "POST": 
        error = ''
        db = get_db()

        try: 
            cur = db.cursor()
            cur.execute('UPDATE channel_list SET talent_name=? WHERE channel_id=?', (request.form['talent_name'], channel_id))

            if cur.rowcount != 1: 
                error = 'Update failed. Please check your input'
                flash(error)
                return redirect(url_for('channels.single_channel', channel_id=channel_id)+'#edit-talent-dialog')
            
            db.commit()
            return redirect(url_for('channels.single_channel', channel_id=channel_id))

        finally: 
            cur.close()


# add talent name for videos without a known talent name
@bp.route('/<channel_id>/add-talent-name')
def add_talent_name(channel_id): 
    add_name(channel_id)
    flash('Talent name added to all videos without a known talent name list. ')
    return redirect(url_for('channels.single_channel', channel_id=channel_id))