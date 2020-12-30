from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, SelectField, TextAreaField, BooleanField, FileField
from models import KegFitting, KegType

__author__ = 'Florian Österreich'


class CreateKeg(FlaskForm):
    name = StringField(u'Name')
    size = IntegerField(u'Fassungsvermögen')
    comment = TextAreaField(u"Kommentar")


class EditKeg(CreateKeg):
    # type = SelectField(u"Typ", coerce=KegType)
    # fitting = SelectField(u"Fitting", coerce=KegFitting)
    isolated = BooleanField(u"Isoliert")
    image = FileField(u"Foto")


class CreateBrew(FlaskForm):
    name = StringField(u'Name')
    date = DateField(u'Brautag', format='%d.%m.%Y')
    size = IntegerField(u'Ausschlagsmenge')


class FillKeg(FlaskForm):
    brew_id = SelectField(u"Sud", coerce=int)
    date = DateField(u"Abfülldatum", format='%d.%m.%Y')


class CommentKeg(FlaskForm):
    location = StringField(u"Ort")
    comment = TextAreaField(u"Kommentar")
    reserved = BooleanField("Reserviert")


class CommentBrew(FlaskForm):
    comment = TextAreaField(u"Kommentar")
