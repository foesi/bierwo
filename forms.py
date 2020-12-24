from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, SelectField

__author__ = 'Florian Österreich'


class CreateKeg(FlaskForm):
    name = StringField(u'Name')
    size = IntegerField(u'Fassungsvermögen')


class CreateBrew(FlaskForm):
    name = StringField(u'Name')
    date = DateField(u'Brautag', format='%d.%m.%Y')
    size = IntegerField(u'Ausschlagsmenge')


class FillKeg(FlaskForm):
    brew_id = SelectField(u"Sud", coerce=int)
    date = DateField(u"Abfülldatum", format='%d.%m.%Y')
