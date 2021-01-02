import io
from flask import Flask, render_template, url_for, request, make_response, send_file, flash
from flask_login import UserMixin, LoginManager, login_required, login_user, logout_user

from models import engine, Keg, Brew, Filling, KegComment, BrewComment, KegFitting, KegType
from forms import CreateKeg, CreateBrew, FillKeg, CommentKeg, CommentBrew, EditKeg, LoginForm, EditBrew
from sqlalchemy.orm import sessionmaker, scoped_session
from werkzeug.utils import redirect
from jinja2 import Template
import qrcode
import datetime
import os
import tempfile
import subprocess

__author__ = 'Florian Österreich'


app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("SECRET") if len(os.getenv("SECRET", default=[])) > 0 else 'geheim'

login_manager = LoginManager()
login_manager.init_app(app)

session = scoped_session(sessionmaker(engine))


class User(UserMixin):
    id = "bier"


@login_manager.user_loader
def load_user(user_id):
    return User()


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.password.data != os.getenv("BIERWO_PASS"):
            flash("Falsches Passwort.")
            return redirect(url_for("login"))

        login_user(User())

        flash('Logged in successfully.')

        next_page = request.args.get('next')

        return redirect(next_page or url_for('list_kegs'))
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("list_kegs"))


@app.teardown_request
def remove_session(ex=None):
    session.remove()


@app.template_filter("last_filling")
def last_filling_filter(value):
    if len(value.fillings) > 0:
        last_filling = sorted(value.fillings, key=lambda b: b.id, reverse=True)[0]
        return last_filling
    return None


@app.template_filter("last_beer")
def last_beer_filter(value):
    last_filling = last_filling_filter(value)
    if last_filling is not None:
        if last_filling.empty_date is None:
            return last_filling.brew.name
        else:
            return "leer"
    return "leer"


@app.template_filter("last_location")
def last_location_filter(value):
    last_comment = sorted(value.keg_comments, key=lambda b: b.timestamp, reverse=True)
    return last_comment[0].location if last_comment is not None and len(last_comment) > 0 else "Keller"


def generate_qrcode(keg_id, path="static/qrcodes/"):
    img = qrcode.make(request.host_url[:-1] + url_for("show_keg", keg_id=keg_id))
    img.save(os.path.join(path, str(keg_id) + ".jpg"), "JPEG")


@app.route("/")
def main():
    return render_template("base.html", title="BierWo?")


@app.route("/kegs/list")
def list_kegs():
    kegs = session.query(Keg).all()
    return render_template("list_kegs.html", kegs=kegs)


@app.route("/kegs/show/<int:keg_id>")
def show_keg(keg_id):
    keg = session.query(Keg).filter_by(id=keg_id).one()
    return render_template("show_keg.html", keg=keg)


@app.route("/kegs/qrcode/generate/<int:keg_id>")
@login_required
def regenerate_qrcode(keg_id):
    generate_qrcode(keg_id)
    return redirect(url_for("show_keg", keg_id=keg_id))


@app.route("/kegs/create", methods=["GET", "POST"])
@login_required
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


@app.route("/kegs/edit/<int:keg_id>", methods=["GET", "POST"])
@login_required
def edit_keg(keg_id):
    form = EditKeg()
    keg = session.query(Keg).filter_by(id=keg_id).one()
    fittings = [(None, "")]
    fittings.extend([(i.value, i.value) for i in KegFitting])
    form.fitting.choices = fittings
    types = [(None, "")]
    types.extend([(i.value, i.value) for i in KegType])
    form.type.choices = types
    if form.validate_on_submit():
        keg.isolated = form.isolated.data

        fitting = None if form.fitting.data == "None" else KegFitting(form.fitting.data)
        keg_type = None if form.type.data == "None" else KegType(form.type.data)
        keg.fitting = fitting
        keg.type = keg_type
        keg.comment = form.comment.data
        if form.image.data is not None:
            image_data = request.files[form.image.name].read()
            keg.photo = image_data
        session.commit()
        return redirect(url_for("list_kegs"))
    else:
        form.name.data = keg.name
        form.size.data = keg.size
        if keg.fitting is not None:
            form.fitting.data = keg.fitting
        if keg.type is not None:
            form.type.data = keg.type
        form.comment.data = keg.comment
        form.isolated.data = keg.isolated
    return render_template("edit_keg.html", form=form, keg=keg)


@app.route("/kegs/comment/create/<int:keg_id>", methods=["GET", "POST"])
@login_required
def create_keg_comment(keg_id):
    form = CommentKeg()
    if form.validate_on_submit():
        new_comment = KegComment()
        new_comment.location = form.location.data
        new_comment.comment = form.comment.data
        new_comment.timestamp = datetime.datetime.now()
        new_comment.keg_id = keg_id
        keg = session.query(Keg).filter_by(id=keg_id).one()
        keg.reserved = form.reserved.data
        session.add(new_comment)
        session.commit()
        return redirect(url_for("show_keg", keg_id=keg_id))
    else:
        keg = session.query(Keg).filter_by(id=keg_id).one()
        form.location.data = last_location_filter(keg)
        form.reserved.data = keg.reserved
    return render_template("create_keg_comment.html", form=form, keg_id=keg_id)


@app.route("/kegs/fill/<int:keg_id>", methods=["GET", "POST"])
@login_required
def fill_keg(keg_id):
    keg = session.query(Keg).filter_by(id=keg_id).one()
    for filling in keg.fillings:
        if filling.empty_date is None :
            flash("Fass ist nicht leer.")
            return redirect(url_for("show_keg", keg_id=keg_id))
    form = FillKeg()
    brews = session.query(Brew).order_by(Brew.date.desc())
    form.brew_id.choices = [(b.id, "%s (%s)" % (b.name, b.date.strftime('%d.%m.%Y'))) for b in brews]
    if form.validate_on_submit():
        new_filling = Filling()
        new_filling.keg_id = keg_id
        new_filling.date = form.date.data
        new_filling.brew_id = form.brew_id.data
        keg.clean = False
        new_comment = KegComment()
        new_comment.location = last_location_filter(keg)
        brew = session.query(Brew).filter_by(id=new_filling.brew_id).one()
        new_comment.comment = "Fass mit %s gefüllt." % brew.name
        new_comment.timestamp = datetime.datetime.now()
        new_comment.keg_id = keg_id
        session.add(new_filling)
        session.add(new_comment)
        session.commit()
        flash("Fass gefüllt.")
        return redirect(url_for("show_keg", keg_id=keg_id))
    else:
        form.date.data = datetime.datetime.now()
    return render_template("fill_keg.html", form=form, keg_id=keg_id)


@app.route("/kegs/empty/<int:keg_id>")
@login_required
def empty_keg(keg_id):
    keg = session.query(Keg).filter_by(id=keg_id).one()
    for filling in keg.fillings:
        filling.empty_date = datetime.datetime.now()
    new_comment = KegComment()
    new_comment.location = last_location_filter(keg)
    new_comment.comment = "Bier %s leer getrunken!" % filling.brew.name
    new_comment.timestamp = datetime.datetime.now()
    new_comment.keg_id = keg_id
    keg.reserved = False
    session.add(new_comment)
    session.commit()
    return redirect(url_for("show_keg", keg_id=keg_id))


@app.route("/kegs/clean/<int:keg_id>")
@login_required
def clean_keg(keg_id):
    keg = session.query(Keg).filter_by(id=keg_id).one()
    keg.clean = True
    new_comment = KegComment()
    new_comment.location = last_location_filter(keg)
    new_comment.comment = "Fass ist gesäubert und vorgespannt."
    new_comment.timestamp = datetime.datetime.now()
    new_comment.keg_id = keg_id
    session.add(new_comment)
    session.commit()
    flash("Fass gereinigt.")
    return redirect(url_for("show_keg", keg_id=keg_id))


@app.route("/brews")
def list_brews():
    brews = session.query(Brew).all()
    return render_template("list_brews.html", brews=brews)


@app.route("/brews/create", methods=["GET", "POST"])
@login_required
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


@app.route("/brews/edit/<int:brew_id>", methods=["GET", "POST"])
@login_required
def edit_brew(brew_id):
    form = EditBrew()
    brew = session.query(Brew).filter_by(id=brew_id).one()
    if form.validate_on_submit():
        brew.comment = form.comment.data
        brew.recipe = form.recipe.data
        brew.original_gravity = form.original_gravity.data
        brew.final_gravity = form.final_gravity.data
        session.commit()
        return redirect(url_for("show_brew", brew_id=brew_id))
    else:
        form.name.data = brew.name
        form.date.data = brew.date
        form.size.data = brew.size
        form.comment.data = brew.comment
        form.recipe.data = brew.recipe
        form.original_gravity.data = brew.original_gravity
        form.final_gravity.data = brew.final_gravity
    return render_template("edit_brew.html", form=form, brew=brew)


@app.route("/brews/show/<int:brew_id>")
def show_brew(brew_id):
    brew = session.query(Brew).filter_by(id=brew_id).one()
    return render_template("show_brew.html", brew=brew)


@app.route("/brews/comment/create/<int:brew_id>", methods=["GET", "POST"])
@login_required
def create_brew_comment(brew_id):
    form = CommentBrew()
    if form.validate_on_submit():
        new_comment = BrewComment()
        new_comment.comment = form.comment.data
        new_comment.timestamp = datetime.datetime.now()
        new_comment.brew_id = brew_id
        session.add(new_comment)
        session.commit()
        return redirect(url_for("show_brew", brew_id=brew_id))
    return render_template("create_brew_comment.html", form=form, brew_id=brew_id)


@app.route("/kegs/qrcode/print")
def print_qrcodes():
    kegs = session.query(Keg).all()
    temp_dir = tempfile.mkdtemp()
    for keg in kegs:
        generate_qrcode(keg.id, path=temp_dir)
    with open("label.tex") as f:
        template = Template(f.read())
        with open(os.path.join(temp_dir, "label.tex"), "w+") as wf:
            wf.write(template.render(kegs=kegs))
    subprocess.run(["pdflatex", "label.tex"], cwd=temp_dir)
    with open(os.path.join(temp_dir, "label.pdf"), "rb") as pdf:
        response = make_response(pdf.read())
        response.headers.set('Content-Disposition', 'attachment', filename="labels.pdf")
        response.headers.set('Content-Type', 'application/pdf')
        return response


@app.route("/kegs/photo/<int:keg_id>")
def show_photo(keg_id):
    keg = session.query(Keg).filter_by(id=keg_id).one()
    return send_file(io.BytesIO(keg.photo),
                     attachment_filename='keg.jpg',
                     mimetype='image/jpg')
