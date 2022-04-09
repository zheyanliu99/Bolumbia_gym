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

from .forms.post import Postform

bp = Blueprint("post", __name__, url_prefix="/post")

def heading_from_dict(res):
    heading = []
    for key in res[0].keys():
        heading.append(key)
    return heading

@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    form = Postform()
    user_id = session["user_id"]
    post = form.post.data
    title = form.title.data
    print(title, post)
    db, cur = get_db()
    cur.execute("""
               SELECT p.post_id, p.title, p.content, p.user_id, p.open_to
               FROM post p JOIN users u
               ON u.user_id = p.user_id""")
    posts = cur.fetchall()
    return render_template("post/postindex.html", posts=posts)


#
def get_post(user_id, check_author=True):
    if user_id != session["user_id"]:
        abort(404)
    db, cur = get_db()
    sql = """
        SELECT p.post_id, p.user_id, p.title, p.content
        from
        (
        SELECT *
        FROM users
        WHERE user_id=%s) a
        INNER JOIN post p
        on a.user_id = p.user_id"""
    cur.execute(sql, (user_id,))
    post = cur.fetchone()

    if post is None:
        abort(404)

    if check_author and post["user_id"] != g.user["user_id"]:
        abort(403)

    return post


# create post
@bp.route("/createpost", methods=("GET", "POST"))
def createpost():
    """Create a new post for the current user."""
    form = Postform()
    user_id = session["user_id"]

    if form.validate_on_submit():
        # flash(form.post.data)
        post = form.post.data
        title = form.title.data

        print('aaaa')
        db, cur = get_db()
        cur.execute(
            "INSERT INTO post (title, content, user_id) VALUES (%s, %s, %s)",
            (title, post, user_id),
        )
        db.commit()
        return redirect(url_for("post.index"))

    return render_template("post/postcreate.html", form = form, user_id = user_id)


#post View
@bp.route('/<int:user_id>')
def postview(user_id):
    if user_id != session["user_id"]:
        abort(404)

    db, cur = get_db()
    sql = """
        WITH post_selected as (
        SELECT post_id, user_id
        FROM post
        WHERE user_id = %s)

        SELECT p.post_id, p.content, p.title, p,datetime, p.open_to
        FROM
        (
        SELECT *
        FROM post_selected p1
        JOIN post p
        ON p.post_id = p1.post_id"""

    cur.execute(sql, (post_id, user_id, content, title))
    postviewing = cur.fetchone()
    post_headings = [key for key in post.keys()]
    post_res = [(postviewing, post_headings) for (postviewing, post_headings) in zip(postviewing, post_headings)]

    return render_template('post/post.html', post_res = post_res)


# update post
@bp.route("/<int:post_id>/update", methods=("GET", "POST"))
def update(post_id):
    user_id = session["user_id"]
    """Update a post if the current user is the author."""
    db, cur = get_db()
    sql = """
        SELECT *
        FROM post
        WHERE post_id = %s AND user_id = %s
        """
    cur.execute(sql, (post_id, user_id))
    post = cur.fetchone()

    form = Postform(
        title = post['title'],
        post = post['content'],
        open_to = post['open_to'],
        date = post['datetime'])

    if form.validate_on_submit():
        title = form.title.data
        post = form.post.data
        open_to = form.open_to.data
        date = form.date.data
        # update sql
        sql = """
            UPDATE post
            SET title = %s, content = %s, open_to = %s, datetime = %s
            WHERE post_id = %s
        """
        cur.execute(sql, (title, post, open_to, date, post_id))
        db.commit()
        flash("updated your post!")
        return redirect(url_for('post.index'))

    return render_template('post/postupdate.html', user_id = user_id, post = post, form = form)


# delete
@bp.route("/<int:post_id>/delete", methods=("POST",))
def delete(post_id):

    user_id = session["user_id"]
    db, cur = get_db()
    sql = """
        SELECT *
        FROM post
        WHERE post_id = %s AND user_id = %s
        """
    cur.execute(sql, (post_id, user_id))
    post = cur.fetchone()
    get_post(user_id)
    db, cur= get_db()
    sql = """
        DELETE FROM post WHERE post_id = %s AND user_id = %s
    """
    cur.execute(sql, (post_id, user_id))
    db.commit()
    flash("Deleted your post!")
    return redirect(url_for("post.index"))
