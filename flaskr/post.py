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

from .forms.post import Postform, Commentform

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
    title = form.title.data
    post = form.post.data
    open_to = form.open_to.data
    date = form.date.data

    commentform = Commentform()
    comment = commentform.comment.data

    db, cur = get_db()
    cur.execute("""
               SELECT p.post_id, p.title, p.content, p.user_id, p.open_to, p.datetime, u.username
               FROM post p JOIN users u
               ON u.user_id = p.user_id""")
    posts = cur.fetchall()

    cur.execute("""
                SELECT c.content, c.post_id, c.user_id
                FROM comment c JOIN post p
                ON c.post_id = p.post_id""")
    comments = cur.fetchall()

    return render_template("post/postindex.html", posts=posts, comments = comments)


@bp.route("/<int:user_id>/Mypost")
def get_post(user_id, check_author=True):
    db, cur = get_db()
    sql = """
        SELECT *
        FROM post
        WHERE user_id = %s
        """
    cur.execute(sql, (user_id, ))
    mypost = cur.fetchall()
    if mypost is None:
        abort(404)

    return render_template("post/mypost.html", mypost=mypost)


# create post
@bp.route("/createpost", methods=("GET", "POST"))
def createpost():
    """Create a new post for the current user."""
    form = Postform()
    user_id = session["user_id"]

    if form.validate_on_submit():
        title = form.title.data
        post = form.post.data
        open_to = form.open_to.data
        date = form.date.data

        print('aaaa')
        db, cur = get_db()
        cur.execute(
            "INSERT INTO post (title, content, open_to, datetime, user_id) VALUES (%s, %s, %s, %s, %s)",
            (title, post, open_to, date, user_id),
        )
        db.commit()
        return redirect(url_for("post.index"))

    return render_template("post/postcreate.html", form = form, user_id = user_id)


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

# createcomment
@bp.route("/createcomment<int:post_id>", methods=("GET", "POST"))
def createcomment(post_id):
    """Create a new comment for posts."""
    form = Commentform()
    user_id = session["user_id"]
    if form.validate_on_submit():
        comment = form.comment.data
        db, cur = get_db()
        cur.execute(
            "INSERT INTO comment (content, post_id, user_id) VALUES (%s, %s, %s)",
            (comment, post_id, user_id),
        )
        db.commit()
        return redirect(url_for('post.index'))

    return render_template('post/postcomment.html', form = form, user_id = user_id, post_id = post_id)
