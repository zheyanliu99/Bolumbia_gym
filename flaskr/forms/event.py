from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, DateField, TimeField, TextAreaField, IntegerField, StringField
from wtforms.validators import DataRequired,Email,EqualTo, length, NumberRange
from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask import flash
import datetime



class SearchEventForm(FlaskForm):
    # place_name = SelectField(u'Workout type', choices=[('cardio room', 'cardio'), ('strength training room', 'strength'), ('swimming pool', 'swimming')])
    startdate = DateField('Start Date', format='%Y-%m-%d', validators=(DataRequired(),))
    enddate = DateField('End Date', format='%Y-%m-%d', validators=(DataRequired(),))
    submit = SubmitField('Search available events')

    def validate_date(self, startdate, enddate):
        if startdate.data > enddate.data:
            flash("Start date must be earlier or equal to end date")
            raise ValidationError("Start date later than end date")
        if startdate.data < datetime.date.today():
            flash("The start date cannot be in the past!")
            raise ValidationError("The date cannot be in the past!")
        if enddate.data > datetime.date.today() + datetime.timedelta(days=30):
            flash("The end date must be within 1 month!")
            raise ValidationError("The date selected is not within 1 month")


class SearchTimeForm(FlaskForm):
    date = DateField("Date", format="%Y-%m-%d",default=datetime.date.today()+datetime.timedelta(days=3), validators=[DataRequired()])
    # date = DateField('Date', format='%Y-%m-%d', validators=(DataRequired(),))
    starttime = TimeField('Earliest start time')
    endtime = TimeField('Latest end time')
    duration = IntegerField('Class duration in minutes', validators=[NumberRange(min=15, max=120), DataRequired()])
    submit = SubmitField('Search availble time')

class CreateEventForm(FlaskForm):
    description = StringField('Description', validators=[length(max=50), DataRequired()])
    classlimit = IntegerField('Age', validators=[NumberRange(min=0, max=12), DataRequired()])
    ageconstraint_lower = IntegerField('Lower age constraint', validators=[NumberRange(min=0, max=100), DataRequired()])
    ageconstraint_upper = IntegerField('Higher age constraint', validators=[NumberRange(min=0, max=100), DataRequired()])
    submit = SubmitField('Submit')