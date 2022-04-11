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

from .forms.QA import Q_Aform, Q_AAnswer

bp = Blueprint("QA", __name__, url_prefix="/QA")

def heading_from_dict(res):
    heading = []
    for key in res[0].keys():
        heading.append(key)
    return heading

@bp.route("/")
def index():
    form = Q_AAnswer()
    user_id = session["user_id"]
    db, cur = get_db()
    cur.execute("""
               SELECT *
               FROM raise_question r JOIN users u
               ON u.user_id = r.user_id
               ORDER BY r.raisedate DESC""")
    Q_A = cur.fetchall()

    cur.execute("""
                SELECT a.admin_id, a.questiontitle_id, a.answer_content, a.answer_time, d.user_id, u.username
                FROM answer a JOIN admin d
                ON a.admin_id = d.admin_id
                LEFT JOIN users u
                ON u.user_id = d.user_id
                ORDER BY a.answer_time DESC""")
    Answer = cur.fetchall()

    cur.execute("""
                SELECT a.user_id, a.admin_id
                From admin a LEFT JOIN users u
                ON u.user_id = a.user_id""")
    admin = cur.fetchall()

    return render_template("QA/QAindex.html", Q_A = Q_A, form = form, Answer = Answer, admin = admin)


# create question
@bp.route("/createquestion", methods=("GET", "POST"))
def createquestion():
    form = Q_Aform()
    user_id = session["user_id"]
    db, cur = get_db()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        date = datetime.datetime.now()

        cur.execute('SELECT max(questiontitle_id) max_questiontitle_id From raise_question')
        max_questiontitle_id = cur.fetchone()['max_questiontitle_id']
        questiontitle_id = max_questiontitle_id + 1

        cur.execute(
            "INSERT INTO raise_question (questiontitle, questioncontent, raisedate, user_id, questiontitle_id) VALUES (%s, %s, %s, %s, %s)",
            (title, content, date, user_id, questiontitle_id),
        )
        db.commit()
        return redirect(url_for("QA.index"))

    return render_template("QA/QAcreate.html", form = form, user_id = user_id)


# delete
@bp.route("/<int:questiontitle_id>/delete", methods=("POST",))
def delete(questiontitle_id):
    user_id = session["user_id"]
    db, cur= get_db()

    sql = """
        DELETE FROM answer WHERE questiontitle_id = %s
    """
    cur.execute(sql, (questiontitle_id, ))
    db.commit()

    sql = """
        DELETE FROM raise_question WHERE questiontitle_id = %s AND user_id = %s
    """
    cur.execute(sql, (questiontitle_id, user_id))
    db.commit()

    flash("Deleted your question!")
    return redirect(url_for("QA.index"))

# create answer
@bp.route("/answer/<int:questiontitle_id>", methods=("GET", "POST"))
def answer(questiontitle_id):
    form = Q_AAnswer()
    user_id = session["user_id"]
    db, cur = get_db()

    cur.execute("SELECT admin_id From admin WHERE user_id = %s", (user_id,))
    admin_id = cur.fetchone()

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
            return redirect(url_for("QA.index"))

    return render_template("QA/QAanswer.html", questiontitle_id = questiontitle_id, form = form, user_id = user_id, admin_id = admin_id)


#edit the answer
@bp.route("/editanswer/<int:questiontitle_id>", methods=("GET", "POST"))
def edit(questiontitle_id):
    user_id = session["user_id"]
    db, cur = get_db()

    sql = """
        SELECT *
        FROM answer
        WHERE questiontitle_id = %s
        """
    cur.execute(sql, (questiontitle_id,))
    Answer = cur.fetchone()

    form = Q_AAnswer(Answer = Answer['answer_content'], date = Answer['answer_time'])

    if form.validate_on_submit():
        Answer = form.Answer.data
        date = datetime.datetime.now()
        # update sql
        sql = """
            UPDATE answer
            SET answer_content = %s, answer_time = %s
            WHERE questiontitle_id = %s
        """
        cur.execute(sql, (Answer, date, questiontitle_id))
        db.commit()
        flash("updated your answer!")
        return redirect(url_for('QA.index'))

    return render_template('QA/QAanswer.html', user_id = user_id, questiontitle_id = questiontitle_id, form = form)

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
    return redirect(url_for("QA.index"))
