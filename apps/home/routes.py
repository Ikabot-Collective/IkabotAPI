from flask import render_template

from apps.home import blueprint


@blueprint.route("/")
def home():
    return render_template("home/index.html")
