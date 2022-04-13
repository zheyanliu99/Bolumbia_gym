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
from forms.QA import Q_AAnswer, Q_Aform

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
        WITH conflict_events as(
        SELECT a.event_id
        FROM
        (
        SELECT *
        FROM event
        WHERE event_id not in (SELECT event_id FROM event_approve)) a,
        (
        SELECT t2.*
        FROM event_approve t1
        INNER JOIN  event t2
        ON t1.event_id = t2.event_id) b
        WHERE a.event_id != b.event_id
        AND a.date = b.date
        AND ((a.endtime > b.starttime AND a.endtime <= b.endtime) OR (a.starttime >= b.starttime AND a.starttime < b.endtime)))

        SELECT d.username coach_name, a.description, starttime, endtime, place_name, classlimit, ageconstraint_lower, ageconstraint_upper, capacity, c.user_id, a.event_id
        FROM
        (
        SELECT *
        FROM event
        WHERE event_id not in (SELECT event_id FROM event_approve)
        AND event_id not in (SELECT event_id FROM conflict_events)) a
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
    timeform = SearchEventForm()
    approved_events = None
    timeform.startdate.default = datetime.date.today()
    timeform.enddate.default = datetime.date.today() + datetime.timedelta(days=14)

    if timeform.validate_on_submit():
        # flash('Here is all the available events')
        # This try except is not necessary, can not work similarly as the routine
        try:
            timeform.validate_date(timeform.startdate, timeform.enddate)
        except:
            pass
        else:
            startdate = timeform.startdate.data
            # startdate = max(datetime.date.today(), startdate)
            # timeform.startdate.data = startdate
            enddate = timeform.enddate.data
            print(startdate, enddate)
            db, cur = get_db()
            sql = """
            WITH event_selected as (
            SELECT *
            FROM event
            WHERE event_id in (SELECT event_id FROM event_approve)
            AND date >= %s
            AND date <= %s)

            SELECT c.user_id, a.event_id, b.description, b.starttime, b.endtime, d.nickname coach_name, a.num_of_users participaters, b.classlimit
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


            cur.execute(sql, (startdate, enddate))
            approved_events = cur.fetchall()
            if request.form.get("shutdownbutton"):
                event_id = request.form['shutdownbutton']
                sql = "DELETE FROM event_approve WHERE event_id = %s"
                try:
                    cur.execute(sql, (event_id, ))
                    db.commit()
                except:
                    flash('You have already shut down this event')
                    return redirect(url_for('admin.eventshutdown'))

    return render_template("admin/eventshutdown.html", approved_events=approved_events, timeform=timeform)

@bp.route("/adminseeQ&A")
def indexQA():
    form = Q_AAnswer()
    user_id = session["user_id"]
    db, cur = get_db()
    cur.execute("""
               SELECT r.*, u.username raisername, u3.username answerername, a.admin_id, a.answer_content
               FROM raise_question r
               INNER JOIN users u
               ON u.user_id = r.user_id
               LEFT JOIN answer a
               ON r.questiontitle_id = a.questiontitle_id
               LEFT JOIN admin u2
               ON a.admin_id = u2.admin_id
               LEFT JOIN users u3
               on u3.user_id = u2.user_id
               ORDER BY r.raisedate DESC""")
    Q_A = cur.fetchall()

    cur.execute("""
                SELECT a.user_id, a.admin_id
                From admin a LEFT JOIN users u
                ON u.user_id = a.user_id""")
    admin = cur.fetchall()

    return render_template("admin/QAindex.html", user_id = user_id, Q_A = Q_A, form = form, admin = admin)


# create answer
@bp.route("/answer/<int:questiontitle_id>", methods=("GET", "POST"))
def answer(questiontitle_id):
    form = Q_AAnswer()
    user_id = session["user_id"]
    db, cur = get_db()

    cur.execute("SELECT * From answer WHERE questiontitle_id = %s", (questiontitle_id,))
    answer = cur.fetchone()

    if answer is None:
        cur.execute("SELECT admin_id From admin WHERE user_id = %s", (user_id,))
        admin_id = cur.fetchone()['admin_id']
        if admin_id is None:
            flash("Only admin can answer the question!")
        else:
            if form.validate_on_submit():
                Answer = form.Answer.data
                date = datetime.datetime.now()
                cur.execute(
                    "INSERT INTO answer (questiontitle_id, answer_content, answer_time, admin_id) VALUES (%s, %s, %s, %s)",
                    (questiontitle_id, Answer, date, admin_id),
                )
                db.commit()
                return redirect(url_for("admin.indexQA"))
    else:
        flash("You can only answer once, you can edit your answer to update it!")

    return render_template("admin/QAanswer.html", answer = answer, questiontitle_id = questiontitle_id, form = form, user_id = user_id)


#edit the answer
@bp.route("/editanswer/<int:questiontitle_id>", methods=("GET", "POST"))
def edit(questiontitle_id):
    user_id = session["user_id"]
    db, cur = get_db()

    cur.execute("SELECT * From answer WHERE questiontitle_id = %s", (questiontitle_id,))
    Answer = cur.fetchone()

    form = Q_AAnswer(Answer = Answer['answer_content'], date = Answer['answer_time'])

    if Answer == None:
        flash("Please Anwser first then update!")
    else:
        if form.validate_on_submit():
            Answer = form.Answer.data
            date = datetime.datetime.now()
            sql = """
                UPDATE answer
                SET answer_content = %s, answer_time = %s
                WHERE questiontitle_id = %s
            """
            cur.execute(sql, (Answer, date, questiontitle_id))
            db.commit()
            flash("updated your answer!")
            return redirect(url_for('admin.indexQA'))

    return render_template('admin/QAanswer.html', user_id = user_id, questiontitle_id = questiontitle_id, form = form)

# delete the answer
@bp.route("/<int:questiontitle_id>/deleteanswer", methods=("POST",))
def deleteanswer(questiontitle_id):
    user_id = session["user_id"]
    db, cur= get_db()

    sql = """
        DELETE FROM answer WHERE questiontitle_id = %s
    """
    cur.execute(sql, (questiontitle_id, ))
    db.commit()

    flash("Deleted your answer!")
    return redirect(url_for("admin.indexQA"))
