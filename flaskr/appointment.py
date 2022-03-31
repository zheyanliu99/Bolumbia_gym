import functools

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
import datetime

from flaskr.db import get_db

from .forms.routine import RoutineForm

bp = Blueprint("appointment", __name__, url_prefix="/appointment")

def heading_from_dict(res):
    heading = []
    for key in res[0].keys():
        heading.append(key)
    return heading


@bp.route('/', methods=['GET', 'POST'])
def manage():
    user_id = session["user_id"]   
    routine_res_heading = None
    event_res_heading = None
    db, cur = get_db()
    start_date = datetime.date.today()
    end_date1 = start_date + datetime.timedelta(days=7)
    end_date2 = start_date + datetime.timedelta(days=30)

    # Routine part
    cur.execute("""
                WITH routine_selected as (
                SELECT routine_id, date, timeslot, sectionname, capacity
                FROM routine  a
                INNER JOIN place b 
                ON a.place_id = b.place_id
                WHERE a.status = 'open'
                AND routine_id  in (SELECT routine_id FROM routine_appointment WHERE user_id = %s)
                AND date >= %s
                AND date <= %s
                AND b.status = 'open')

                SELECT a.routine_id,  sectionname section, date, timeslot, num_of_users participaters, capacity 
                FROM
                (
                SELECT t1.routine_id, count(distinct user_id)  as num_of_users
                FROM routine_selected t1
                LEFT JOIN routine_appointment t2
                ON t1.routine_id = t2.routine_id
                GROUP BY t1.routine_id) a
                INNER JOIN routine_selected b
                ON a.routine_id = b.routine_id
                WHERE num_of_users < capacity
                ORDER BY b.date""", (user_id, start_date, end_date1))
    routine_res = cur.fetchall() 
    if routine_res:
        routine_res_heading = heading_from_dict(routine_res)

    # Event part
    cur.execute("""
                WITH event_selected as (
                SELECT * 
                FROM event 
                WHERE event_id in (SELECT event_id FROM event_appointment WHERE user_id = %s)
                AND date >= %s
                AND date <= %s)

                SELECT a.event_id, b.description as event, b.starttime, b.endtime, d.nickname coach_name, a.num_of_users participaters, b.classlimit
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
                ORDER BY b.starttime""", (user_id, start_date, end_date2))
    event_res = cur.fetchall() 
    if event_res:
        event_res_heading = heading_from_dict(event_res)


    # Delete routine
    if request.form.get("routinecancel"):
        routine_id = request.form.get('routinecancel')
        try:
            cur.execute(
                "DELETE FROM routine_appointment WHERE user_id = %s AND routine_id = %s;",
                (user_id, routine_id),
            )
            db.commit()
        except Exception as e:
            # The username was already taken, which caused the
            # commit to fail. Show a validation error.
            print(e)
            flash("Cancel failure, you have cancelled this routine appointment before")

    # Delete event
    if request.form.get("eventcancel"):
        event_id = request.form.get('eventcancel')
        try:
            cur.execute(
                "DELETE FROM event_appointment WHERE user_id = %s AND event_id = %s;",
                (user_id, event_id),
            )
            db.commit()
        except Exception as e:
            # The username was already taken, which caused the
            # commit to fail. Show a validation error.
            print(e)
            flash("Cancel failure, you have cancelled this event appointment before")


    return render_template('appointment/appointment.html', routine_res=routine_res, routine_res_heading=routine_res_heading, event_res=event_res, event_res_heading=event_res_heading)
