from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, DateField, TextAreaField
from wtforms.validators import DataRequired,Email,EqualTo
from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask import flash
import datetime



class Postform(FlaskForm):
    title = StringField('title', validators=(DataRequired(),))
    post = TextAreaField('post', validators=(DataRequired(),))
    open_to = SelectField(u'open_to', choices=[('everyone', 'everyone'), ('just myself', 'just myself')], validators=(DataRequired(),))
    date = DateField('Date', format='%Y-%m-%d', validators=(DataRequired(),))
    submit = SubmitField('sumbit posts')
