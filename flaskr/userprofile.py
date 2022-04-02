import datetime
import functools

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from flaskr.db import get_db


bp = Blueprint("userprofile", __name__, url_prefix="/userprofile")

def heading_from_dict(res):
    heading = []
    for key in res[0].keys():
        heading.append(key)
    return heading


@bp.route('/<int:user_id>', methods=['GET', 'POST'])
def show(user_id):
    
    current_user_id = session["user_id"]
    if_current_user = current_user_id == user_id
    coaching_info_more = None
    db, cur = get_db() 
    # Get user info
    cur.execute("SELECT username, nickname, email, sex, age FROM users WHERE user_id = %s", (user_id, ))
    user_info = cur.fetchone()

    cur.execute("SELECT count(*) as followers FROM follow_record WHERE user_id = %s", (user_id, ))
    followers = cur.fetchone()

    cur.execute("SELECT count(*) as following FROM follow_record WHERE follower_id = %s", (user_id, ))
    following = cur.fetchone()

    # Get coach info
    cur.execute("SELECT * FROM coach WHERE user_id = %s", (user_id, ))
    coaching_info = cur.fetchone()

    if coaching_info:
        sql = """
            SELECT count(*) events, sum(participators) participators
            FROM
            (
                SELECT * FROM event 
                WHERE coach_id = %s
                AND date <= %s)a
            INNER JOIN 
            (
                SELECT event_id, count(distinct user_id) participators
                FROM event_appointment
                GROUP BY event_id
            ) b 
            ON a.event_id = b.event_id"""
                    
        cur.execute(sql, (coaching_info['coach_id'], datetime.date.today()))
        coaching_info_more = cur.fetchone()
   
    return render_template('userprofile/userprofile.html', user_id=user_id, if_current_user=if_current_user, 
        user_info=user_info, followers=followers, following=following, coaching_info=coaching_info, coaching_info_more=coaching_info_more)
