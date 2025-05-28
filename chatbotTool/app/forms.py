from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, validators
from wtforms.validators import DataRequired, InputRequired, Length

class ChatForm(FlaskForm):
    questionText = TextAreaField('Some Text:', render_kw={"id": "questionText","placeholder": "Enter question here", "rows": 5, "class": "form-control full-width", "style": "resize:none;"}, validators=[DataRequired()])
    submit = SubmitField('Submit')
    export = SubmitField('Export Chat')
    reset = SubmitField('Reset Chat')

class PasswordForm(FlaskForm):
    password = PasswordField('Password:', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Submit')