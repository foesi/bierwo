from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, BooleanField, FileField, PasswordField
from wtforms.validators import optional
from wtforms.fields.html5 import IntegerField, DateField, URLField, DecimalField

__author__ = 'Florian Österreich'


class LoginForm(FlaskForm):
    password = PasswordField(u"Passwort")


class CreateKeg(FlaskForm):
    name = StringField(u'Name')
    size = IntegerField(u'Fassungsvermögen')
    comment = TextAreaField(u"Kommentar")


class EditKeg(CreateKeg):
    type = SelectField(u"Typ")
    fitting = SelectField(u"Fitting")
    isolated = BooleanField(u"Isoliert")
    image = FileField(u"Foto")


class CreateBrew(FlaskForm):
    name = StringField(u'Name')
    date = DateField(u'Brautag')
    size = IntegerField(u'Ausschlagsmenge')


class EditBrew(CreateBrew):
    comment = TextAreaField(u"Informationen")
    recipe = URLField(u"Rezept")
    protocol = FileField(u"Brauprotokoll")
    original_gravity = DecimalField(u"Stammwürze (% Brix)", validators=[optional()])
    final_gravity = DecimalField(u"Extrakt Jungbier (% Brix)", validators=[optional()])


class FillKeg(FlaskForm):
    brew_id = SelectField(u"Sud", coerce=int)
    date = DateField(u"Abfülldatum")


class CommentKeg(FlaskForm):
    location = StringField(u"Ort")
    comment = TextAreaField(u"Kommentar")
    reserved = BooleanField("Reserviert")


class CommentBrew(FlaskForm):
    comment = TextAreaField(u"Kommentar")
