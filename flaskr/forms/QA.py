from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, DateField, TextAreaField
from wtforms.validators import DataRequired,Email,EqualTo, length
from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask import flash
import datetime



class Q_Aform(FlaskForm):
    title = StringField('Title', validators=(DataRequired(),))
    content = TextAreaField('Question', validators=(DataRequired(), length(max=200), ))
#    date = DateField('raisedate', format='%Y-%m-%d', validators=(DataRequired(),))
    submit = SubmitField('Sumbit Question')

class Q_AAnswer(FlaskForm):
    Answer = TextAreaField('Answer', validators=(DataRequired(), length(max=200), ))
#    date = DateField('raisedate', format='%Y-%m-%d', validators=(DataRequired(),))
    submit = SubmitField('Sumbit')
