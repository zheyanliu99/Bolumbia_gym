from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, StringField, IntegerField, RadioField, TextAreaField
from wtforms.validators import DataRequired,Email,EqualTo, NumberRange, length
from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask import flash
import datetime



class UserProfileForm(FlaskForm):
    nickname = StringField('Nickname')
    email = StringField('Email', validators=[Email()])
    age = IntegerField('Age', validators=[NumberRange(min=0, max=100)])
    sex = RadioField('Sex', choices=[('male','male'), ('female','female'), ('other','other')])
    picture = FileField('Update Avatar *only allow png format', validators=[FileAllowed(['png'])])
    description = TextAreaField('Description', validators=[length(max=500)])
    submit = SubmitField('Submit')


class BecomeCoachForm(FlaskForm):
    experienceyears = IntegerField('Experience in years', validators=[NumberRange(min=0, max=100)]) 
    description = TextAreaField('Description', validators=[length(max=500)])
    submit = SubmitField('Submit')