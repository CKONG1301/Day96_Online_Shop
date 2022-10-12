from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired, FileField
from wtforms import StringField, SubmitField, SelectField, TextAreaField, IntegerField, DecimalField, EmailField, PasswordField
from wtforms.validators import DataRequired

CHOICES = ['Audio', 'Appliance', 'Others']
QTY = [*range(1, 6)]


class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


class NewProductForm(FlaskForm):
    category = SelectField('Category', validators=[DataRequired()], choices=CHOICES)
    title = StringField('Title', default='ML-20', validators=[DataRequired()])
    stock = IntegerField('Stock', default=20, validators=[DataRequired()])
    price = DecimalField('Price', default=3.5, validators=[DataRequired()])
    description = TextAreaField('Description', default='Stereo Speaker.', validators=[DataRequired()], render_kw={'rows': 5})
    file = FileField('Select Image File:', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'bmp'], 'Images only!')], render_kw={'class': 'form-control-file'})
    submit = SubmitField('Save')


class PurchaseForm(FlaskForm):
    qty = SelectField('Qty', validators=[DataRequired()], choices=QTY)
    submit = SubmitField('    BUY    ')
    