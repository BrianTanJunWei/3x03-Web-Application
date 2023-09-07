from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/newpage1')
def page1():
    return 'Testing routing'

@app.route('/newpage2')
def page2():
    return 'Testing routing to page 2'