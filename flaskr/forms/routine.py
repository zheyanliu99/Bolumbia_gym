from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, DateField
from wtforms.validators import DataRequired,Email,EqualTo
from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask import flash
import datetime



class RoutineForm(FlaskForm):
    place_name = SelectField(u'Workout type', choices=[('cardio room', 'cardio'), ('strength training room', 'strength'), ('swimming pool', 'swimming')], validators=(DataRequired(),))
    date = DateField('Date', format='%Y-%m-%d', validators=(DataRequired(),))
    submit = SubmitField('Search available routines')

    def validate_date(self, field):
        if field.data < datetime.date.today():
            flash("The date cannot be in the past!")
            raise ValidationError("The date cannot be in the past!")
        if field.data > datetime.date.today() + datetime.timedelta(days=7):
            flash("The date must be within 1 week!")
            raise ValidationError("The date selected is not within 1 week")
        


