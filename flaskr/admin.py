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

from flaskr.db import get_db

from .forms.event import SearchEventForm, CreateEventForm, SearchTimeForm

bp = Blueprint("admin", __name__, url_prefix="/admin")

def heading_from_dict(res):
    heading = []
    for key in res[0].keys():
        heading.append(key)
    return heading


@bp.route('/', methods=['GET', 'POST'])
def index():
    user_id = session['user_id']
    db, cur = get_db()
    cur.execute("SELECT * FROM admin WHERE user_id=%s", (user_id,))
    res = cur.fetchone()
    if not res:
        abort(404)
    print('****************', session['admin_id'])
    return render_template("admin/index.html")


@bp.route('/event/approve', methods=['GET', 'POST'])
def eventapprove():
    db, cur = get_db()
    sql = """
        SELECT d.username coach_name, a.description, starttime, endtime, place_name, classlimit, ageconstraint_lower, ageconstraint_upper, capacity, c.user_id, a.event_id 
        FROM
        (
        SELECT a.*
        FROM     
        (
        SELECT * 
        FROM event 
        WHERE event_id not in (SELECT event_id FROM event_approve)
        AND starttime > %s) a, 
        (
        SELECT t2.* 
        FROM event_approve t1
        INNER JOIN  event t2
        ON t1.event_id = t2.event_id) b
        WHERE a.event_id != b.event_id 
        AND a.date = b.date
        AND ((a.endtime > b.starttime AND a.endtime <= b.endtime) OR (a.starttime >= b.starttime AND a.starttime < b.endtime))) a
        INNER JOIN place p
        ON a.place_id = p.place_id
        INNER JOIN coach c 
        ON a.coach_id = c.coach_id
        INNER JOIN users d 
        ON c.user_id = d.user_id
        ORDER BY starttime

    """
    cur.execute(sql, (datetime.datetime.now(), ))
    unapproved_events = cur.fetchall()

    if request.form.get("approvebutton"):
        event_id = request.form['approvebutton']
        admin_id = session['admin_id']
        sql = "INSERT INTO event_approve values (%s, %s, %s)"
        try:
            cur.execute(sql, (event_id, admin_id, datetime.datetime.now()))
            db.commit()
        except:
            flash('You have already approve this event')
        return redirect(url_for('admin.eventapprove'))

    return render_template("admin/eventapprove.html", unapproved_events = unapproved_events)


@bp.route('/event/eventshutdown', methods=['GET', 'POST'])
def eventshutdown():
    pass