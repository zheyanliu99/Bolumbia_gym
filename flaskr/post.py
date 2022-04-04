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


bp = Blueprint("post", __name__, url_prefix="/post")

def heading_from_dict(res):
    heading = []
    for key in res[0].keys():
        heading.append(key)
    return heading


@bp.route('/post', methods=['GET', 'POST'])
def post():
    form = Postform()
    headings = None
    res = None
    user_id = session["user_id"]

    if form.validate_on_submit():
        form.validate_on_submit(form.post)
        db, cur = get_db()
        cur.execute("""
            SELECT *
            FROM post AS p
            INNER JOIN
            SELECT post_id
            FROM users_post AS U
            on p.user.id = U.user_id""", (user_id, post_id, content))
        res = cur.fetchall()
        if not res:
            flash("No available event, try another date")
        else:
            headings = heading_from_dict(res)
            if request.form.get("submitbutton"):
                post_id = request.form.get('submitbutton')
                print(post_id, user_id)
                try:
                    cur.execute(
                        "INSERT INTO content (user_id, post_id) VALUES (%s, %s)",
                        (user_id, post_id),
                    )
                    db.commit()
                except Exception as e:
                    print(e)
                    # This could happen if user clicks too quick...should find a way to solve that
                    flash("post failure")


#    cur.execute("SELECT username, nickname, email FROM users WHERE user_id = %s", (user_id, ))
#    user_info = cur.fetchone()

#    cur.execute("SELECT content FROM post WHERE user_id = %s", (user_id, ))
#    post = cur.fetchone()

    return render_template('post/post.html', form = form)
