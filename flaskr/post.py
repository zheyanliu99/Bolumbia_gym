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

from .forms.post import Postform, Commentform, Likeform

bp = Blueprint("post", __name__, url_prefix="/post")

def heading_from_dict(res):
    heading = []
    for key in res[0].keys():
        heading.append(key)
    return heading

@bp.route("/")
def index():
    user_id = session['user_id']
    """Show all the posts, most recent first."""

    db, cur = get_db()

    cur.execute("""
               SELECT p.post_id, p.title, p.content, p.user_id, p.open_to, p.datetime, u.username
               FROM post p 
               JOIN users u
               ON u.user_id = p.user_id
               WHERE post_id in (SELECT post_id
                                    FROM post 
                                    WHERE open_to = 'everyone'
                                    UNION
                                    SELECT post_id
                                    FROM post 
                                    WHERE open_to = 'myself'
                                    AND user_id = %s
                                    UNION
                                    SELECT post_id
                                    FROM post 
                                    WHERE open_to = 'followers'
                                    AND %s in (SELECT follower_id FROM 
                                                (
                                                SELECT user_id FROM post
                                                WHERE open_to = 'followers') a
                                                INNER JOIN follow_record b
                                                ON a.user_id = b.user_id))
               ORDER BY p.datetime DESC""", (user_id, user_id))
    posts = cur.fetchall()

    cur.execute("""
                SELECT c.content, c.post_id, c.user_id, c.if_anonymous, u.username
                FROM comment c JOIN post p
                ON c.post_id = p.post_id
                INNER JOIN users u
                ON p.user_id = u.user_id""")
    comments = cur.fetchall()

    cur.execute("""
                SELECT L.if_like, L.post_id, L.user_id
                FROM liked L JOIN post p
                ON L.post_id = p.post_id""")
    liked = cur.fetchall()

    # like and dislike count
    cur.execute("""
            SELECT p.post_id, SUM(CASE WHEN if_like = True THEN 1 ELSE 0 END) like_sum, SUM(CASE WHEN if_like = False THEN 1 ELSE 0 END) dislike_sum
            FROM post p
            LEFT JOIN liked l
            ON p.post_id = l.post_id
            GROUP BY p.post_id""")
    like_dislike_sum = cur.fetchall()
    like_dislike_dict = {}
    for alike_dislike_sum in like_dislike_sum:
        like_dislike_dict[alike_dislike_sum['post_id']] = {'like_sum':alike_dislike_sum['like_sum'], 'dislike_sum':alike_dislike_sum['dislike_sum']}

    # if a user has liked or disliked
    cur.execute("""
            SELECT post_id FROM liked WHERE user_id = %s""", (user_id, ))
    responsed_post = cur.fetchall()

    return render_template("post/postindex.html", user_id=user_id, posts=posts, comments = comments, like_dislike_dict = like_dislike_dict, liked = liked, responsed_post=responsed_post)


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
    db, cur = get_db()

    if form.validate_on_submit():
        title = form.title.data
        post = form.post.data
        open_to = form.open_to.data
        time = datetime.datetime.now()

        # serial not working...
        cur.execute('SELECT max(post_id) max_post_id From post')
        max_post_id = cur.fetchone()['max_post_id']
        post_id = max_post_id + 1
        cur.execute(
            "INSERT INTO post (post_id, title, content, open_to, datetime, user_id) VALUES (%s,%s, %s, %s, %s, %s)",
            (post_id, title, post, open_to, time, user_id),
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
        open_to = post['open_to'])

    if form.validate_on_submit():
        title = form.title.data
        post = form.post.data
        open_to = form.open_to.data
        time = datetime.datetime.now()
        # update sql
        sql = """
            UPDATE post
            SET title = %s, content = %s, open_to = %s, datetime = %s
            WHERE post_id = %s
        """
        cur.execute(sql, (title, post, open_to, time, post_id))
        db.commit()
        flash("updated your post!")
        return redirect(url_for('post.index'))

    return render_template('post/postupdate.html', user_id = user_id, post = post, form = form)


# delete
@bp.route("/<int:post_id>/delete", methods=("POST",))
def delete(post_id):
    user_id = session["user_id"]
    db, cur= get_db()

    sql = """
        DELETE FROM comment WHERE post_id = %s AND user_id = %s
    """
    cur.execute(sql, (post_id, user_id))
    db.commit()

    sql = """
        DELETE FROM liked WHERE post_id = %s AND user_id = %s
    """
    cur.execute(sql, (post_id, user_id))
    db.commit()

    sql = """
        DELETE FROM post WHERE post_id = %s AND user_id = %s
    """
    cur.execute(sql, (post_id, user_id))
    db.commit()

    flash("Deleted your post and all comments!")
    return redirect(url_for("post.index"))

# createcomment
@bp.route("/createcomment<int:post_id>", methods=("GET", "POST"))
def createcomment(post_id):
    """Create a new comment for posts."""
    form = Commentform()
    user_id = session["user_id"]
    if form.validate_on_submit():
        comment = form.comment.data
        if_anonymous = form.anonymous.data

        db, cur = get_db()
        cur.execute(
            "INSERT INTO comment (content, post_id, user_id, if_anonymous) VALUES (%s, %s, %s, %s)",
            (comment, post_id, user_id, if_anonymous),
        )
        db.commit()
        # flash("Your comment and all comments!")
        return redirect(url_for('post.index'))

    return render_template('post/postcomment.html', form = form, user_id = user_id, post_id = post_id)

# # create like or dislike
# @bp.route("/likeornot<int:post_id>", methods=("GET", "POST"))
# def like(post_id):
#     form = Likeform()
#     user_id = session["user_id"]
#     if form.validate_on_submit():
#         like = form.like.data
#         db, cur = get_db()

#         # prevent duplicate key in application level
#         cur.execute(
#             "INSERT INTO liked (if_like, post_id, user_id) VALUES (%s, %s, %s)",
#             (like, post_id, user_id),
#         )
#         db.commit()
#         return redirect(url_for('post.index'))

#     return render_template('post/postlike.html', form = form, user_id = user_id, post_id = post_id)


# like button
@bp.route("/like/<int:post_id>", methods=("GET", "POST"))
def like(post_id):
    user_id = session["user_id"]
    like = True
    db, cur = get_db()

    # prevent duplicate key in application level
    cur.execute(
        "INSERT INTO liked (if_like, post_id, user_id) VALUES (%s, %s, %s)",
        (like, post_id, user_id),
    )
    db.commit()
    
    return redirect(url_for('post.index'))

# dislike button
@bp.route("/dislike/<int:post_id>", methods=("GET", "POST"))
def dislike(post_id):
    user_id = session["user_id"]
    like = False
    db, cur = get_db()

    # prevent duplicate key in application level
    cur.execute(
        "INSERT INTO liked (if_like, post_id, user_id) VALUES (%s, %s, %s)",
        (like, post_id, user_id),
    )
    db.commit()
    
    return redirect(url_for('post.index'))