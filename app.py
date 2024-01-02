from flask import Flask
import time
from src.token.getToken import getToken

app = Flask(__name__)

@app.route('/')
def welcome():
    return 'Welcome to the Ikabot API!'

@app.route('/get_token',methods = ['GET'])
def get_token_route():
        start_time = time.time()
        token = getToken()
        print("Token generated in %s seconds" % (time.time() - start_time))
        return token

if __name__ == '__main__':
    app.run()