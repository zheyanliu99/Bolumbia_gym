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
from .forms.userprofile import UserProfileForm

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
    if_follow = None 

    db, cur = get_db() 
    # If follow
    cur.execute("SELECT * FROM follow_record WHERE user_id = %s AND follower_id = %s", (user_id, current_user_id))
    if_follow = cur.fetchone()

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


    # Follow/Unfollow button

    if request.method == 'POST':
        if request.form['follow_button'] == 'Follow':
            try:
                cur.execute("INSERT INTO follow_record  VALUES (%s, %s, %s)",(user_id, current_user_id, datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S')))
                db.commit()
            except Exception as e:
                # The username was already taken, which caused the
                # commit to fail. Show a validation error.
                print(e)
                flash("Follow failure, you have followed this user")

        elif request.form['follow_button'] == 'Unfollow':
            try:
                cur.execute("DELETE FROM follow_record WHERE user_id = %s AND follower_id = %s",(user_id, current_user_id))
                db.commit()
            except Exception as e:
                # The username was already taken, which caused the
                # commit to fail. Show a validation error.
                print(e)
                flash("Unfollow failure, you do not follow this user")

        return redirect(url_for('userprofile.show', user_id=user_id))
    return render_template('userprofile/userprofile.html', user_id=user_id, current_user_id=current_user_id, if_current_user=if_current_user, if_follow=if_follow,
        user_info=user_info, followers=followers, following=following, coaching_info=coaching_info, coaching_info_more=coaching_info_more)


@bp.route('/<int:user_id>/follower', methods=['GET', 'POST'])
def followers(user_id):
    if user_id != session["user_id"]:
        abort(404)
    db, cur = get_db() 
    sql = """
        SELECT b.user_id, b.username, nickname, email, a.datetime follow_time
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

    
    return render_template('userprofile/follower.html', followers=followers, followers_headings=followers_headings)

@bp.route('/<int:user_id>/following', methods=['GET', 'POST'])
def following(user_id):
    if user_id != session["user_id"]:
        abort(404)
    db, cur = get_db() 
    sql = """
        SELECT b.user_id, b.username, nickname, email, a.datetime follow_time
        FROM
        (
        SELECT * 
        FROM follow_record 
        WHERE follower_id=%s) a
        INNER JOIN users b
        ON a.user_id = b.user_id
        ORDER BY datetime DESC"""
           
    cur.execute(sql, (user_id,))
    followers = cur.fetchall()
    followers_headings = heading_from_dict(followers)

    
    return render_template('userprofile/following.html', followers=followers, followers_headings=followers_headings)

@bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
def edit(user_id):
    # A user cannot edit others profile
    if user_id != session["user_id"]:
        abort(404)
    db, cur = get_db() 
    cur.execute("SELECT * FROM USERS WHERE user_id=%s", (user_id,))
    user_info = cur.fetchone()
    # Set default values for forms
    form = UserProfileForm(
        nickname = user_info['nickname'],
        email = user_info['email'],
        age = user_info['age'],
        sex = user_info['sex'])

    cur.execute("SELECT * FROM coach WHERE user_id=%s", (user_id,))
    coach_info = cur.fetchone()

    if coach_info:
        form.description.default = coach_info['description']

    
    if form.validate_on_submit():
        nickname = form.nickname.data
        email = form.email.data
        age = form.age.data
        sex = form.sex.data
        # update sql
        sql = """
            UPDATE users
            SET nickname = %s, email = %s, age = %s, sex = %s
            WHERE user_id = %s    
        """
        cur.execute(sql, (nickname, email, age, sex, user_id))
        db.commit()
        # update if coach 
        if coach_info:
            print('working on coach')
            description = form.description.data
            sql = """
                UPDATE coach
                SET description = %s
                WHERE user_id = %s    
            """
            cur.execute(sql, (description, user_id))            
            db.commit()
        
        flash("Profile updated")
        return redirect(url_for('userprofile.show', user_id=user_id))

    return render_template('userprofile/edit.html', form=form, coach_info=coach_info)