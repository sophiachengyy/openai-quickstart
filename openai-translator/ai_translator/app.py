import os
import csv
import json
from flask import Flask, flash, url_for, request, abort, redirect, render_template, send_from_directory, session
from flask_restful import Api, Resource
from flasgger import Swagger, swag_from
from flask_cors import CORS
from werkzeug.utils import secure_filename
from markupsafe import escape

from translator import PDFTranslator
from model import OpenAIModel

app = Flask(__name__)
api = Api(app)
swagger = Swagger(app)

CORS(app, resources={r"/api/*": {"origins": "*"}})
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = '/usr/sophia/temp/flaskTempUpload/'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def validate_user(username, password):
    with open('data/users.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if row['username'] == username and row['password'] == password:
                return True
    return False

@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html', username=escape(session['username']))
    return redirect(url_for('login'))

@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    username = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if validate_user(username, password):
            session['username'] = username
            return render_template('login_ok.html', username=username)
        else:
            error = 'Invalid username/password'
    return render_template('login.html', message=error, username=username)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/session_username')
def check_session():
    if 'username' in session:
        return session['username']
    else:
        abort(401)

@app.route('/upload', methods=['GET'])
def upload():
    return render_template('upload.html')

@app.route('/uploads/<filename>', methods=['GET'])
def file_uploaded(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class FileUploadAndTranslate(Resource):
    @swag_from({
        'parameters': [
            {
                'name': 'file',
                'in': 'formData',
                'type': 'file',
                'required': True,
                'description': 'File to upload and translate'
            },
            {
                'name': 'file_type',
                'in': 'formData',
                'type': 'string',
                'required': True,
                'description': 'Type of the file'
            },
            {
                'name': 'target_language',
                'in': 'formData',
                'type': 'string',
                'required': True,
                'description': 'Target language for translation'
            },
            {
                'name': 'target_format',
                'in': 'formData',
                'type': 'string',
                'required': True,
                'description': 'Target format for translated file'
            }
        ],
        'responses': {
            200: {
                'description': 'Translation result',
                'schema': {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'integer'},
                        'msg': {'type': 'string'},
                        'data': {'type': 'string'}
                    }
                }
            },
            400: {
                'description': 'Invalid input'
            }
        }
    })
    def post(self):
        if 'file' not in request.files:
            return {'status': 1, 'msg': 'No file part'}, 400
        file = request.files['file']
        if file.filename == '':
            return {'status': 2, 'msg': 'No selected file'}, 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            file_type = request.form['file_type']
            target_language = request.form['target_language']
            target_format = request.form['target_format']
            filefullname = filename + '.' + file_type

            newModel = OpenAIModel(model='gpt-3.5-turbo', api_key=os.getenv('OPENAI_API_KEY'))
            translator = PDFTranslator(newModel)
            input_filename= os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(f'input_filename={input_filename}')
            output_file_path = translator.translate_pdf(input_filename, target_language=target_language, file_format=target_format)
            print(f'output_file_path={output_file_path}')
            output_filename = os.path.basename(output_file_path)
            print(f'output_filename={output_filename}')

            return {'status': 0, 'msg': 'success', 'data': output_filename}
        return {'status': 3, 'msg': 'Not allowed file type'}, 400

api.add_resource(FileUploadAndTranslate, '/api/v1/files/translate')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
