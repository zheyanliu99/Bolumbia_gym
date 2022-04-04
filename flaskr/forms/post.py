from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, DateField, TextAreaField
from wtforms.validators import DataRequired,Email,EqualTo
from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask import flash
import datetime



class Postform(FlaskForm):

    post = TextAreaField()
    submit = SubmitField('Search available events',validators=(DataRequired(),))
