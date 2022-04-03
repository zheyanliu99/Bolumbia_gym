from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, StringField, IntegerField, RadioField, TextAreaField
from wtforms.validators import DataRequired,Email,EqualTo, NumberRange, length
from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask import flash
import datetime



class UserProfileForm(FlaskForm):
    # place_name = SelectField(u'Workout type', choices=[('cardio room', 'cardio'), ('strength training room', 'strength'), ('swimming pool', 'swimming')])
    nickname = StringField('Nickname')
    email = StringField('Email', validators=[Email()])
    age = IntegerField('Age', validators=[NumberRange(min=0, max=100)])
    sex = RadioField('Sex', choices=[('male','male'), ('female','female'), ('other','other')])
    description = TextAreaField('Description', validators=[length(max=500)])
    submit = SubmitField('Submit')