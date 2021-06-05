import traceback

from flask import Flask, request, render_template, send_from_directory
from flask_cors import CORS
from db.model import db, Files
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

ERR_DESCRIPTION = os.environ.get('ERR_DESC', 'none')
RULES_JSON = os.environ.get('RULES_JSON', os.path.join(os.path.dirname(npttf2utf.__file__), 'map.json'))
FLUSH_KEY = os.environ.get('FLUSH_KEY', ''.join(random.choice(string.ascii_letters) for x in range(32)))
UPLOADS_LIFESPAN = int(os.environ.get('FILE_LIFESPAN', '60')) * 60
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
font_mapper = npttf2utf.FontMapper(RULES_JSON)


# Create storage directories if missing
def create_dirs():
    if not os.path.isdir(UPLOADED_FILES_STORAGE):
        os.makedirs(UPLOADED_FILES_STORAGE)
    if not os.path.isdir(PROCESSED_FILES_STORAGE):
        os.makedirs(PROCESSED_FILES_STORAGE)


# Get error description as specified from err_desc env var
def gendesc(e=None):
    if ERR_DESCRIPTION == 'traceback':
        return traceback.format_exc()
    elif ERR_DESCRIPTION == 'exc_name':
        return str(e)
    else:
        return None


# WebApp routes
@app.route('/static/<string:file_name>', methods=['GET'])
def serve_static(file_name):
    try:
        return send_from_directory('static', file_name)
    except:
        return {'message': 'Nothing here !'}, 404


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html', file_life=str(UPLOADS_LIFESPAN / 60))


@app.route('/upload', methods=['POST'])
def upload():
    uploaded_file = request.files['document']
    file_extension = uploaded_file.filename.split('.')[-1]
    internal_name = file_key = ''.join(random.choice(string.ascii_letters) for x in range(32))

    if file_extension in supported_file_types.keys() and uploaded_file.filename != '':
        try:
            uploaded_file.save(os.path.join(UPLOADED_FILES_STORAGE, internal_name + '.' + file_extension))
            detected_fonts = supported_file_types[file_extension].detect_used_fonts(
                UPLOADED_FILES_STORAGE + internal_name + '.' + file_extension)
            file_in_db = Files(file_key, uploaded_file.filename, internal_name + '.' + file_extension, file_extension)
            db.session.add(file_in_db)
            db.session.commit()
            return {'file_id': file_key,
                    'detected_supported_fonts': detected_fonts,
                    'supported_origins': supported_file_types[file_extension].supported_ttf_fonts,
                    'supported_targets': ['Unicode', 'Preeti']}, 200
        except Exception as e:
            db.session.flush()
            db.session.rollback()
            return {'message': 'Internal error ', 'description': gendesc(e)}, 500
    else:
        return {'message': 'No support for provided file type'}, 403


@app.route('/processtext', methods=['POST', 'GET'])
def map_text():
    origin_font = request.form.get("origin", "Preeti") if request.method == "POST" \
        else request.args.get("origin", "Preeti")
    target_font = request.form.get("target", "Unicode") if request.method == "POST" \
        else request.args.get("target", "Unicode")
    text = request.form['text'] if request.method == "POST" else request.args['text']

    if target_font.lower() == "preeti":
        try:
            text = font_mapper.map_to_preeti(text, from_font=origin_font)
            return {"text": text}, 200
        except npttf2utf.NoMapForOriginException:
            return {"message": "Cannot map to preeti from origin font '" + origin_font + "'"}, 403
        except Exception as e:
            return {'message': 'Internal error ', 'description': gendesc(e)}, 500
    elif target_font.lower() == "unicode":
        try:
            text = font_mapper.map_to_unicode(text, from_font=origin_font)
            return {"text": text}, 200
        except npttf2utf.NoMapForOriginException:
            return {"message": "Cannot map to preeti from origin font '" + origin_font + "'"}, 403
        except Exception as e:
            return {'message': 'Internal error ', 'description': gendesc(e)}, 500
    else:
        return {"message": "Cannot map to selected target font '" + target_font + "'"}, 403


@app.route('/process', methods=['POST'])
def process():
    origin_font = request.form['origin']
    target_font = request.form['target']
    file_key = request.form['file_id']
    file_in_db = Files.query.filter(Files.file_key == file_key, Files.processed == False,
                                    Files.uploaded_on >= int(time.time()) - UPLOADS_LIFESPAN).first()
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
                return {'message': 'Unsupported font to map from', 'description': None}, 500
            except npttf2utf.UnsupportedMapToException:
                return {'message': 'Cannot map to provided font/type face. Unsupported !', 'description': None}, 500
            except npttf2utf.TxtAutoModeException:
                return {'message': 'Font auto-convert not available for this file type', 'description': None}, 500
            except Exception as e:
                return {'message': 'Internal error. Contact administrator with this token (' + file_key + ')',
                        'token': file_key, 'description': gendesc(e)}, 500
        else:
            return {'message': 'No support for provided file type'}, 403
    else:
        return {'message': 'File not found, already processed or more than 60 minutes elapsed after upload'}, 404


@app.route('/download/<string:file_key>', methods=['GET'])
def download(file_key):
    file_in_db = Files.query.filter(Files.file_key == file_key, Files.processed == True,
                                    Files.uploaded_on >= int(time.time()) - UPLOADS_LIFESPAN).first()
    if file_in_db:
        try:
            return send_from_directory(PROCESSED_FILES_STORAGE,
                                       file_in_db.internal_name,
                                       as_attachment=True,
                                       attachment_filename=file_in_db.orginal_name)
        except Exception as e:
            return {'message': 'Internal error! File not found on server, Contact administrators',
                    'description': gendesc(e)}, 500
    else:
        return {'message': 'File not found, not processed or more than 60 minutes elapsed after upload'}, 404


@app.route('/flush_files/<string:param_flush_key>', methods=['GET'])
def flush(param_flush_key):
    if param_flush_key == FLUSH_KEY:
        try:
            files_in_db = Files.query.filter(Files.uploaded_on <= int(time.time()) - UPLOADS_LIFESPAN,
                                             Files.isdeleted is False)
            for file in files_in_db:
                if os.path.exists(UPLOADED_FILES_STORAGE + file.internal_name):
                    os.remove(UPLOADED_FILES_STORAGE + file.internal_name)
                if os.path.exists(PROCESSED_FILES_STORAGE + file.internal_name):
                    os.remove(PROCESSED_FILES_STORAGE + file.internal_name)
                file.isdeleted = True
                db.session.commit()
        except Exception as e:
            db.session.flush()
            return {'message': 'Internal error ', 'description': gendesc(e)}, 500
    return {'message': 'Done'}, 200

create_dirs()
with app.app_context():
    db.create_all()
    
if __name__ == '__main__':

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
    app.run(debug=bool(int(os.environ.get("DEBUG", "0"))), host=os.environ.get('HOST', '0.0.0.0'),
            port=int(os.environ.get('PORT', '5000')))
