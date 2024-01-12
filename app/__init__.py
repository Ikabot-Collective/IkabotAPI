import logging
import time
from PIL import Image
import traceback
import threading


from flask import Flask, jsonify, request, abort

from app.lobby_captcha.image import break_interactive_captcha
from app.pirates_captcha.ikapiratesdecaptcha import get_captcha_string
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

    def Captcha_detection(image):

    # write to disk
    with open('temppiratecaptcha.png','wb') as file:
        file.write(image.read())

    curr = time.time()
    result = get_captcha_string('temppiratecaptcha.png')
    print('detect_image done, elapsed: ', str(time.time() - curr ), ' result: ', result)
    return result

    @app.route('/ikagod/ikabot', methods=['POST'])
    def home():
    try:
        if 'upload_file' in request.files:
            threadqueue.append(threading.current_thread().ident)
            print(threading.active_count())
            while True:
                with lock:
                    if threading.current_thread().ident == threadqueue[-1]:
                        captcha = Captcha_detection(request.files['upload_file'])
                        threadqueue.remove(threading.current_thread().ident)
                        break
                    else:
                        time.sleep(0.01)

        elif 'text_image' in request.files and 'drag_icons' in request.files:
            text_image = request.files['text_image'].read()
            drag_icons = request.files['drag_icons'].read()
            try:
                captcha = break_interactive_captcha(text_image, drag_icons)
                print('SUCCESSFULLY SOLVED INTERACTIVE CAPTCHA WITH NEW FUNC, RESULT: ' + str(captcha) )
            except:
                print('FAILED TO SOLVE INTERACTIVE CAPTCHA WITH NEW FUNC')
                print(traceback.format_exc())
                captcha = 'Error'

        else:
            abort(400)
        return str(captcha)
    except Exception as e:
        print(traceback.format_exc())
        return 'Error'

    app.logger.info("Ikabot API ready!")
    return app
