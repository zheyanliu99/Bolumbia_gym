import functools

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from marshmallow import ValidationError

from flaskr.db import get_db

from .forms.event import SearchEventForm

bp = Blueprint("event", __name__, url_prefix="/event")

def heading_from_dict(res):
    heading = []
    for key in res[0].keys():
        heading.append(key)
    return heading


@bp.route('/book', methods=['GET', 'POST'])
def book():
    form = SearchEventForm()
    res = None
    headings = None 
    user_id = session["user_id"]

    if form.validate_on_submit():
        # flash('Here is all the available events')
        # This try except is not necessary, can not work similarly as the routine
        try:
            form.validate_date(form.startdate, form.enddate)
        except:
            pass
        else:
            startdate = form.startdate.data 
            enddate = form.enddate.data
            print(startdate, enddate)
            db, cur = get_db()

            sql = """
                WITH event_selected as (
                SELECT * 
                FROM event 
                WHERE event_id not in (SELECT event_id FROM event_appointment WHERE user_id = %s)
                AND date >= %s
                AND date <= %s)

                SELECT a.event_id, b.description, b.starttime, b.endtime, d.nickname coach_name, a.num_of_users participaters, b.classlimit
                FROM
                (
                SELECT t1.event_id, count(distinct user_id)  as num_of_users
                FROM event_selected t1
                LEFT JOIN event_appointment t2
                ON t1.event_id = t2.event_id
                GROUP BY t1.event_id) a
                INNER JOIN event_selected b
                ON a.event_id = b.event_id 
                INNER JOIN coach c
                ON b.coach_id = c.coach_id
                INNER JOIN users d
                ON c.user_id = d.user_id
                WHERE num_of_users < classlimit
                ORDER BY b.starttime"""
            
            cur.execute(sql, (user_id, startdate, enddate))
            res = cur.fetchall()
            if not res:
                flash("No available event, try another date")
            else:
                headings = heading_from_dict(res)

                if request.form.get("bookbutton"):
                    event_id = request.form.get('bookbutton')
                    # print(event_id, user_id)
                    try:
                        cur.execute(
                            "INSERT INTO event_appointment (user_id, event_id) VALUES (%s, %s)",
                            (user_id, event_id),
                        )
                        db.commit()
                    except Exception as e:
                        # The username was already taken, which caused the
                        # commit to fail. Show a validation error.
                        print(e)
                        flash("Book failure, you have booked this event appointment before")
                
    return render_template('event/book.html', form=form, headings=headings, res=res)


@bp.route('/<int:event_id>')
def event_info(event_id):
    # grab the requested blog post by id number or return 404
    db, cur = get_db()
    sql = """
        WITH event_selected as (
        SELECT * 
        FROM event 
        WHERE event_id = %s)

        SELECT b.description, p.place_name place, b.starttime, b.endtime, d.nickname coach_name, a.num_of_users participaters, b.classlimit
        FROM
        (
        SELECT t1.event_id, count(distinct user_id)  as num_of_users
        FROM event_selected t1
        LEFT JOIN event_appointment t2
        ON t1.event_id = t2.event_id
        GROUP BY t1.event_id) a
        INNER JOIN event_selected b
        ON a.event_id = b.event_id 
        INNER JOIN coach c
        ON b.coach_id = c.coach_id
        INNER JOIN users d
        ON c.user_id = d.user_id
        INNER JOIN place p
        ON b.place_id = p.place_id
        ORDER BY b.starttime"""
            
    cur.execute(sql, (event_id,))
    events = cur.fetchone()
    event_headings = [key for key in events.keys()]
    events_res = [(event, event_heading) for (event, event_heading) in zip(events, event_headings)]
    return render_template('event/event.html', events_res=events_res)
