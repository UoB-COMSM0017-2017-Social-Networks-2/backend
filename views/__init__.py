from flask import render_template

from main import app
from views.authentication import *
from views.data import *


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/application')
def application():
    return render_template('application.html')
