from flask import Flask, render_template, url_for, request
from models import engine, Keg, Brew, Filling, KegComment
from forms import CreateKeg, CreateBrew, FillKeg, CommentKeg
from sqlalchemy.orm import sessionmaker, scoped_session
from werkzeug.utils import redirect
import qrcode
import datetime
import os

__author__ = 'Florian Österreich'


app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("SECRET") if len(os.getenv("SECRET", default=[])) > 0 else 'geheim'

session = scoped_session(sessionmaker(engine))


@app.teardown_request
def remove_session(ex=None):
    session.remove()


@app.template_filter("last_beer")
def last_beer_filter(value):
    if not value.empty:
        last_filling = sorted(value.fillings, key=lambda b: b.id, reverse=True)[0]
        return last_filling.brew.name

    return "Leer"


@app.template_filter("last_location")
def last_location_filter(value):
    last_comment = sorted(value.keg_comments, key=lambda b: b.timestamp, reverse=True)
    return last_comment[0].location if last_comment is not None and len(last_comment) > 0 else "Keller"


def generate_qrcode(keg_id):
    img = qrcode.make(request.host_url[:-1] + url_for("show_keg", keg_id=keg_id))
    img.save("static/qrcodes/" + str(keg_id) + ".jpg", "JPEG")


@app.route("/")
def main():
    return render_template("base.html", title="BierWo?")


@app.route("/kegs/list")
def list_kegs():
    kegs = session.query(Keg).filter(Keg.empty == False).all()
    empty_kegs = session.query(Keg).filter(Keg.empty).all()
    return render_template("list_kegs.html", kegs=kegs, empty_kegs=empty_kegs)


@app.route("/kegs/show/<int:keg_id>")
def show_keg(keg_id):
    keg = session.query(Keg).filter_by(id=keg_id).one()
    return render_template("show_keg.html", keg=keg)


@app.route("/kegs/qrcode/generate/<int:keg_id>")
def regenerate_qrcode(keg_id):
    generate_qrcode(keg_id)
    return redirect(url_for("show_keg", keg_id=keg_id))


@app.route("/kegs/create", methods=["GET", "POST"])
def create_keg():
    form = CreateKeg()
    if form.validate_on_submit():
        new_keg = Keg()
        new_keg.name = form.name.data
        new_keg.size = form.size.data
        session.add(new_keg)
        session.commit()
        generate_qrcode(new_keg.id)
        return redirect(url_for("list_kegs"))
    return render_template("create_keg.html", form=form)


@app.route("/kegs/comment/create/<int:keg_id>", methods=["GET", "POST"])
def create_keg_comment(keg_id):
    form = CommentKeg()
    if form.validate_on_submit():
        new_comment = KegComment()
        new_comment.location = form.location.data
        new_comment.comment = form.comment.data
        new_comment.timestamp = datetime.datetime.now()
        new_comment.keg_id = keg_id
        session.add(new_comment)
        session.commit()
        return redirect(url_for("show_keg", keg_id=keg_id))
    else:
        keg = session.query(Keg).filter_by(id=keg_id).one()
        form.location.data = last_location_filter(keg)
    return render_template("create_keg_comment.html", form=form, keg_id=keg_id)


@app.route("/kegs/fill/<int:keg_id>", methods=["GET", "POST"])
def fill_keg(keg_id):
    form = FillKeg()
    brews = session.query(Brew).order_by(Brew.date.desc())
    form.brew_id.choices = [(b.id, "%s (%s)" % (b.name, b.date.strftime('%d.%m.%Y'))) for b in brews]
    if form.validate_on_submit():
        new_filling = Filling()
        new_filling.keg_id = keg_id
        new_filling.date = form.date.data
        new_filling.brew_id = form.brew_id.data
        keg = session.query(Keg).filter_by(id=keg_id).one()
        keg.empty = False
        session.add(new_filling)
        session.commit()
        return redirect(url_for("show_keg", keg_id=keg_id))
    else:
        form.date.data = datetime.datetime.now()
    return render_template("fill_keg.html", form=form, keg_id=keg_id)


@app.route("/kegs/empty/<int:keg_id>")
def empty_keg(keg_id):
    keg = session.query(Keg).filter_by(id=keg_id).one()
    keg.empty = True
    session.commit()
    return redirect(url_for("show_keg", keg_id=keg_id))


@app.route("/brews")
def list_brews():
    brews = session.query(Brew).all()
    return render_template("list_brews.html", brews=brews)


@app.route("/brews/create", methods=["GET", "POST"])
def create_brew():
    form = CreateBrew()
    if form.validate_on_submit():
        new_brew = Brew()
        new_brew.name = form.name.data
        new_brew.date = form.date.data
        new_brew.size = form.size.data
        session.add(new_brew)
        session.commit()
        return redirect(url_for("list_brews"))
    return render_template("create_brew.html", form=form)

