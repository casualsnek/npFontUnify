from flask import Flask, request, render_template, send_from_directory
from flask_cors import CORS
from db.model import db, files
import npttf2utf
import os
import random
import string
import time
import json

app = Flask(__name__)
CORS(app)

app.secret_key = os.environ.get('SECRET_KEY', ''.join(random.choice(string.ascii_letters) for x in range(32)))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI', 'sqlite:///db.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

RULES_JSON = os.environ.get('RULES_JSON', os.path.join(os.path.dirname(npttf2utf.__file__), 'map.json'))
FLUSH_KEY = os.environ.get('FLUSH_KEY', ''.join(random.choice(string.ascii_letters) for x in range(32)))
UPLOADS_LIFESPAN = int(os.environ.get('FILE_LIFESPAN', '3600'))
DEFAULT_UNICODE_FONT = os.environ.get('DEFAULT_UNICODE_FONT', 'Kalimati')
UPLOADED_FILES_STORAGE = os.environ.get('UPLOAD_LOCATION', os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                                        'user_files',
                                                                        'uploads', ''))
PROCESSED_FILES_STORAGE = os.environ.get('PROCESSED_LOCATION', os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                                            'user_files',
                                                                            'processed', ''))

supported_file_types = {}

# Create a instance of file handler classes and add file extension and its handler to dictionary
docx = npttf2utf.DocxHandler(RULES_JSON, default_unicode_font_name=DEFAULT_UNICODE_FONT)
txt = npttf2utf.TxtHandler(RULES_JSON)
supported_file_types['docx'] = docx
supported_file_types['txt'] = txt


# Create storage directories if missing
def create_dirs():
    if not os.path.isdir(UPLOADED_FILES_STORAGE):
        os.makedirs(UPLOADED_FILES_STORAGE)
    if not os.path.isdir(PROCESSED_FILES_STORAGE):
        os.makedirs(PROCESSED_FILES_STORAGE)


# WebApp routes
@app.route('/static/<string:file_name>', methods=['GET'])
def serve_static(file_name):
    try:
        return send_from_directory('static', file_name)
    except:
        return {'message': 'Nothing here !'}, 404


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')


@app.route('/upload', methods=['POST'])
def upload():
    uploaded_file = request.files['document']
    file_extension = uploaded_file.filename.split('.')[-1]
    internal_name = ''.join(random.choice(string.ascii_letters) for x in range(32))
    file_key = ''.join(random.choice(string.ascii_letters) for x in range(32))

    if file_extension in supported_file_types.keys() and uploaded_file.filename != '':
        try:
            uploaded_file.save(os.path.join(UPLOADED_FILES_STORAGE, internal_name + '.' + file_extension))
            detected_fonts = supported_file_types[file_extension].detect_used_fonts(
                UPLOADED_FILES_STORAGE + internal_name + '.' + file_extension)
            file_in_db = files(file_key, uploaded_file.filename, internal_name + '.' + file_extension, file_extension)
            db.session.add(file_in_db)
            db.session.commit()
            return {'file_id': file_key,
                    'detected_supported_fonts': detected_fonts,
                    'supported_origins': supported_file_types[file_extension].supported_ttf_fonts,
                    'supported_targets': ['Unicode', 'Preeti']}, 200
        except Exception as e:
            db.session.flush()
            db.session.rollback()
            return {'message': 'Internal error ' + str(e)}, 500
    else:
        return {'message': 'No support for provided file type'}, 403


@app.route('/process', methods=['POST'])
def process():
    origin_font = request.form['origin']
    target_font = request.form['target']
    file_key = request.form['file_id']
    file_in_db = files.query.filter(files.file_key == file_key, files.processed == False,
                                    files.uploaded_on >= int(time.time()) - UPLOADS_LIFESPAN).first()
    if file_in_db:
        if file_in_db.ftype in supported_file_types:
            components = json.loads(request.form.get('process_components', '["body_paragraph", "table", "shape"]'))
            try:
                supported_file_types[file_in_db.ftype].map_fonts(os.path.join(UPLOADED_FILES_STORAGE,
                                                                              file_in_db.internal_name),
                                                                 output_file_path=os.path.join(
                                                                     PROCESSED_FILES_STORAGE,
                                                                     file_in_db.internal_name),
                                                                 from_font=origin_font, to_font=target_font,
                                                                 components=components)
                file_in_db.processed = True
                db.session.commit()
                return {'message': 'success', 'download_uri': 'download/' + file_key}, 200
            except npttf2utf.NoMapForOriginException:
                return {'message': 'Unsupported font to map from'}, 500
            except npttf2utf.UnsupportedMapToException:
                return {'message': 'Cannot map to provided font/type face. Unsupported !'}, 500
            except npttf2utf.TxtAutoModeException:
                return {'message': 'Font auto-convert not available for this file type'}, 500
            except:
                return {'message': 'Internal error. Contact administrator with this token (' + file_key + ')',
                        'token': file_key}, 500
        else:
            return {'message': 'No support for provided file type'}, 403
    else:
        return {'message': 'File not found, already processed or more than 60 minutes elapsed after upload'}, 404


@app.route('/download/<string:file_key>', methods=['GET'])
def download(file_key):
    file_in_db = files.query.filter(files.file_key == file_key, files.processed == True,
                                    files.uploaded_on >= int(time.time()) - UPLOADS_LIFESPAN).first()
    if file_in_db:
        try:
            return send_from_directory(PROCESSED_FILES_STORAGE,
                                       file_in_db.internal_name,
                                       as_attachment=True,
                                       attachment_filename=file_in_db.orginal_name)
        except:
            return {'message': 'Critical error! File not found on server, Contact administrators'}
    else:
        return {'message': 'File not found, not processed or more than 60 minutes elapsed after upload'}, 404


@app.route('/flush_files/<string:param_flush_key>', methods=['GET'])
def flush(param_flush_key):
    if param_flush_key == FLUSH_KEY:
        try:
            files_in_db = files.query.filter(files.uploaded_on <= int(time.time()) - UPLOADS_LIFESPAN,
                                             files.isdeleted is False)
            for file in files_in_db:
                if os.path.exists(UPLOADED_FILES_STORAGE + file.internal_name):
                    os.remove(UPLOADED_FILES_STORAGE + file.internal_name)
                if os.path.exists(PROCESSED_FILES_STORAGE + file.internal_name):
                    os.remove(PROCESSED_FILES_STORAGE + file.internal_name)
                file.isdeleted = True
                db.session.commit()
        except:
            db.session.flush()
            return {'message': 'Internal error.'}, 500
    return {'message': 'Done'}, 200


if __name__ == '__main__':
    create_dirs()
    with app.app_context():
        db.create_all()
    print("""
    --------------- npFontUnify ---------------
      Using Rule file          : {}
      Default unicode font     : {}
      File lifespan set to     : {} seconds
      Saving uploaded file in  : {}
      Saving processed file in : {}
      Supported file types     : {}
    -------------------------------------------
    """.format(RULES_JSON, DEFAULT_UNICODE_FONT, str(UPLOADS_LIFESPAN), UPLOADED_FILES_STORAGE, PROCESSED_FILES_STORAGE,
               str(supported_file_types.keys())))
    app.run(debug=True, host=os.environ.get('HOST', '0.0.0.0'), port=int(os.environ.get('PORT', '5000')))
