from flask import jsonify

from apps.home import blueprint


@blueprint.route("/")
def home():
    return jsonify("Welcome to the Ikabot API!")
