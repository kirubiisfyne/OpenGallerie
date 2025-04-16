from flask import Flask, render_template
import requests
import json

app = Flask(__name__)

@app.route('/')

def index():
    return render_template('index.html')

app.run(host="0.0.0.0", port=5000, debug=True)
# This code creates a simple Flask web application that returns "Hello, World!" when accessed at the root URL.