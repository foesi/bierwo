from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, BooleanField, FileField, PasswordField
from wtforms.validators import optional
from wtforms.fields import IntegerField, DateField, DecimalField, URLField, StringField

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
    deprecated = BooleanField(u"Ausgemustert")
    isolated = BooleanField(u"Isoliert")
    fermenter = BooleanField(u"Gärfass")
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
    location = SelectField(u"Ort", validate_choice=False)
    comment = TextAreaField(u"Kommentar")
    reserved = BooleanField("Reserviert")


class CommentBrew(FlaskForm):
    comment = TextAreaField(u"Kommentar")
