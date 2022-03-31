from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, DateField
from wtforms.validators import DataRequired,Email,EqualTo
from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask import flash
import datetime



class SearchEventForm(FlaskForm):
    # place_name = SelectField(u'Workout type', choices=[('cardio room', 'cardio'), ('strength training room', 'strength'), ('swimming pool', 'swimming')])
    startdate = DateField('Start Date', format='%Y-%m-%d', validators=(DataRequired(),))
    enddate = DateField('End Date', format='%Y-%m-%d', validators=(DataRequired(),))
    submit = SubmitField('Search for available event')

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