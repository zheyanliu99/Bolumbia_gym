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
from flask import abort

from flaskr.db import get_db


bp = Blueprint("userprofile", __name__, url_prefix="/userprofile")

def heading_from_dict(res):
    heading = []
    if len(res) == 0:
        pass
    elif len(res) == 1:
        return  [key for key in res.keys()]
    else:
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


@bp.route('/<int:user_id>/follower', methods=['GET', 'POST'])
def followers(user_id):
    if user_id != session["user_id"]:
        abort(404)
    db, cur = get_db() 
    sql = """
        SELECT b.user_id, b.username, a.datetime follow_time
        FROM
        (
        SELECT * 
        FROM follow_record 
        WHERE user_id=%s) a
        INNER JOIN users b
        ON a.follower_id = b.user_id
        ORDER BY datetime DESC"""

            
    cur.execute(sql, (user_id,))
    followers = cur.fetchall()
    followers_headings = heading_from_dict(followers)

    if request.form.get("more"):
        user_id_more = request.form.get('more')
        return redirect(url_for('userprofile.show', user_id=user_id_more))
    
    return render_template('userprofile/follower.html', followers=followers, followers_headings=followers_headings)
    

