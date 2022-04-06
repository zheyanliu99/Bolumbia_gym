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
               SELECT p.post_id, p.title, p.content, p.author_id, p.open_to
               FROM post p JOIN users u
               ON u.user_id = p.author_id""")
    posts = cur.fetchall()
    return render_template("post/postindex.html", posts=posts)


#
def get_post(user_id, check_author=True):
    db, cur = get_db()
    cur.execute("""
                SELECT p.post_id, title, content, user_id FROM post AS p
                JOIN users_post AS u
                ON p.post_id = u.post_id
                WHERE post_id = %s""", (user_id, post_id))
    post = cur.fetchone()

    if post is None:
        abort(404)

    if check_author and post["user_id"] != g.user["user_id"]:
        abort(403)

    return post


# CREATE POST
#@bp.route('/createpost', methods=['GET', 'POST'])
#def createpost():
#    form = Postform()
#    res = None
#    headings = None
#    user_id = session["user_id"]
#    post = form.post.data
#    title = form.title.data

#    if form.validate_on_submit():
#        db, cur = get_db()
#        headings = heading_from_dict(res)
#        if request.form.get("bookbutton"):
#            post_id = request.form.get('bookbutton')
#            try:
#                cur.execute(
#                    "INSERT INTO users_post (user_id, post_id) VALUES (%s, %s)",
#                    (user_id, post_id),
#                )
#                db.commit()
#                return redirect(url_for(postview))
#            except Exception as e:
#                # The username was already taken, which caused the
#                # commit to fail. Show a validation error.
#                print(e)
#                flash("post failure")
#    return render_template('post/postcreate.html', form=form, headings = headings,
#                            user_id = user_id, title = title)
# create post
@bp.route("/createpost", methods=("GET", "POST"))
def createpost():
    """Create a new post for the current user."""
    form = Postform()
    user_id = session["user_id"]

    if form.validate_on_submit():
        flash(form.post.data)
        post = form.post.data
        title = form.title.data
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db, cur = get_db()
            cur.execute(
                "INSERT INTO post (title, content, author_id) VALUES (%s, %s, %s)",
                (title, content, user_id),
            )
            db.commit()
            return redirect(url_for("post.index"))

    return render_template("post/postcreate.html")


#post View
@bp.route('/<int:user_id>')
def postview(user_id):
    if user_id != session["user_id"]:
        abort(404)

    db, cur = get_db()
    sql = """
        WITH post_selected as (
        SELECT post_id, user_id
        FROM users_post
        WHERE user_id = %s)

        SELECT p.post_id, p.content, p.title, p,datetime, p.open_to
        FROM
        (
        SELECT *
        FROM post_selected p1
        JOUN post p
        ON p.post_id = p1.post_id"""

    cur.execute(sql, (post_id, user_id, content, title))
    postviewing = cur.fetchone()
    post_headings = [key for key in post.keys()]
    post_res = [(postviewing, post_headings) for (postviewing, post_headings) in zip(postviewing, post_headings)]

    return render_template('post/post.html', post_res = post_res)


#update
#@bp.route('/<int:post_id>/update', methods=['GET', 'POST'])
#def updatepost(post_id):
#    post = post.query.get_or_404(post_id)
#
#    if post.post_id != current_user:
#        abort(403)
#    form = Postform()
#
#    if form.validate_on_submit():
#        post.Title = form.Title.data
#        post.Content = form.Content.data
#        cur.execute(
#            "INSERT INTO post (title, content) VALUES (%s, %s)",
#            (title, content, user_id),
#        )
#        db.commit()
#
#    return render_template('post/postcreate.html', form=form)#
#
#
#    return render_template('post/post.html', form = form)

# update post
@bp.route("/<int:user_id>/update", methods=("GET", "POST"))
def update(user_id):
    """Update a post if the current user is the author."""
    post = get_post(user_id)

    if request.method == "POST":
        title = request.form["title"]
        post = request.form["post"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db, cur = get_db()
            cur.execute(
                "UPDATE post SET title = %s, body = %s WHERE user_id = %s", (title, content, user_id)
            )
            db.commit()
            return redirect(url_for("post.index"))

    return render_template("post/update.html", post=post)


# delete
@bp.route("/<int:post_id>/delete", methods=("POST",))
def delete(post_id):
    """Delete a post.
    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("blog.index"))
