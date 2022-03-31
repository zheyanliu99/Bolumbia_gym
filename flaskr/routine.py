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

from .forms.routine import RoutineForm

bp = Blueprint("routine", __name__, url_prefix="/routine")

def heading_from_dict(res):
    heading = []
    for key in res[0].keys():
        heading.append(key)
    return heading


@bp.route('/book', methods=['GET', 'POST'])
def book():
    form = RoutineForm()
    res = None
    headings = None 
    user_id = session["user_id"]

    place_name = form.place_name.data
    date = form.date.data 
    # print(place_name, date, type(date))

    if form.validate_on_submit():
        flash('Here is all the available routine')
        form.validate_date(form.date)
        # return redirect(url_for('users.login'))
        db, cur = get_db()
        cur.execute("""
            WITH routine_selected as (
            SELECT routine_id, date, timeslot, sectionname, capacity
            FROM routine  a
            INNER JOIN place b 
            ON a.place_id = b.place_id
            WHERE a.status = 'open'
            AND routine_id not in (SELECT routine_id FROM routine_appointment WHERE user_id = %s)
            AND b.status = 'open'
            AND date = %s
            AND place_name = %s)

            SELECT a.routine_id, date, timeslot, sectionname section, num_of_users participaters, capacity 
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
            ORDER BY b.date""", (user_id, date, place_name))
        res = cur.fetchall()
        if res:
            headings = heading_from_dict(res)
    
    # if request.form.get("book"):
    #     print('Book ID: ', request.form.get('book'))
        if request.form.get("bookbutton"):
            routine_id = request.form.get('bookbutton')
            print(routine_id, user_id)
            try:
                cur.execute(
                    "INSERT INTO routine_appointment (user_id, routine_id) VALUES (%s, %s)",
                    (user_id, routine_id),
                )
                db.commit()
            except Exception as e:
                # The username was already taken, which caused the
                # commit to fail. Show a validation error.
                print(e)
                flash("Book failure, you have booked this routine appointment before")
                
    return render_template('routine/book.html', form=form, headings=headings, res=res)
