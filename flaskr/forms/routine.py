from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, DateField
from wtforms.validators import DataRequired,Email,EqualTo
from wtforms import ValidationError
from flask_wtf.file import FileField, FileAllowed



class RoutineForm(FlaskForm):
    place_name = SelectField(u'Workout type', choices=[('cardio room', 'cardio'), ('strength training room', 'strength'), ('swimming pool', 'swimming')])
    date = DateField('Date', format='%Y-%m-%d')
    submit = SubmitField('Search for availability')


