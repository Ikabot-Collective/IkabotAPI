import logging
import time

from flask import Flask, jsonify

from app.token.TokenGenerator import TokenGenerator

token_generator = TokenGenerator()


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    app.logger.setLevel(logging.INFO)

    @app.route("/")
    def welcome():
        return jsonify("Welcome to the Ikabot API!")

    @app.route("/new_token", methods=["GET"])
    def new_token_route():
        try:
            start_time = time.time()
            token = token_generator.get_token()
            app.logger.info(
                "Token generated in %s seconds" % (time.time() - start_time)
            )
            return jsonify(token), 200
        except Exception as e:
            app.logger.error(e)
            return (
                jsonify(
                    {
                        "status": "erreur",
                        "message": f"An error occurred during the token generation: {e}",
                    }
                ),
                500,
            )

    # This message is used to check if the API is ready in the deployment pipeline
    app.logger.info("Ikabot API ready!")
    return app
