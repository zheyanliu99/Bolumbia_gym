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
from flask_restful import abort
from marshmallow import ValidationError
import sys
import logging 
logging.basicConfig(level=logging.DEBUG)

from db import get_db

from forms.event import SearchEventForm, CreateEventForm, SearchTimeForm

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

                SELECT a.event_id, b.description, b.starttime, b.endtime, d.nickname coach_name, a.num_of_users participants, b.classlimit, CONCAT(b.ageconstraint_lower, '~',b.ageconstraint_upper) recommend_age
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
                        # return redirect(url_for('event.book'))
                    
                
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

        SELECT d.user_id, b.description, p.place_name place, b.starttime, b.endtime, d.nickname coach_name, a.num_of_users participaters, b.classlimit
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

@bp.route('/create', methods=['GET', 'POST'])
def create():
    timeform = SearchTimeForm()
    eventform = None
    available_times = []
    step = 0
    # timeform.date.default = datetime.date.today() + datetime.timedelta(days=3)
    
    # if coach
    db, cur = get_db()
    cur.execute("SELECT * FROM coach WHERE user_id=%s", (session['user_id'], ))
    coach_info = cur.fetchall()
    print(coach_info)
    
    # search time form
    if timeform.validate_on_submit():
        step = 1
        flash(timeform.date.data)
        place_id = timeform.place.data
        date = timeform.date.data
        starttime = timeform.starttime.data
        endtime = timeform.endtime.data
        duration = timeform.duration.data
        starttimep = datetime.datetime(date.year, date.month, date.day, starttime.hour, starttime.minute, starttime.second) 
        endtimep = datetime.datetime(date.year, date.month, date.day, endtime.hour, endtime.minute, endtime.second) 
        sql = """
            SELECT starttime, endtime 
            FROM event
            WHERE date = %s
            AND event_id in (SELECT event_id FROM Event_approve)
            AND place_id = %s """
                    
        cur.execute(sql, (date, place_id, ))
        unavailable_times = cur.fetchall()

        # available time list
        stattime_list = [datetime.datetime(date.year, date.month, date.day, h, 0, 0) for h in range(9, 21)]
        stattime_list = [time for time in stattime_list if time >= starttimep and time <= endtimep]
        available_times = []
        time_id = 0
        for tstart in stattime_list:
            tend = tstart + datetime.timedelta(minutes=duration)
            tflag = True 
            for unavailable_time in unavailable_times:
                if (tend > unavailable_time['starttime'] and tend <= unavailable_time['endtime']) or (tstart >= unavailable_time['starttime'] and tstart < unavailable_time['endtime']):
                    tflag = False
                    break
            if tflag:
                available_times.append({'time_id':time_id, 'starttime':tstart, 'endtime':tend})
                time_id += 1

        # details form
        eventform = CreateEventForm()
        if eventform.validate_on_submit():
            time_id = request.form.get('selected_time')
            print(type(time_id))
            if not time_id:
                print('Please select time')
            else:
                time_id = int(request.form['selected_time'])
                timeselected = [a for a in available_times if a['time_id'] == time_id][0]
                description = eventform.description.data 
                classlimit = eventform.classlimit.data
                ageconstraint_lower = eventform.ageconstraint_lower.data 
                ageconstraint_upper = eventform.ageconstraint_upper.data                
                sql = """
                    INSERT INTO event (coach_id, date, place_id, starttime, endtime, description, classlimit, ageconstraint_lower, ageconstraint_upper) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                cur.execute(sql, (coach_info[0]['coach_id'], date, place_id, timeselected['starttime'], timeselected['endtime'], description, classlimit, ageconstraint_lower, ageconstraint_upper))
                db.commit()
    return render_template('event/create.html', coach_info=coach_info, user_id=session['user_id'], timeform=timeform, eventform=eventform, available_times=available_times, step=step)
