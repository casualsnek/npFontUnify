import logging
import os
import random
import string
import time
import json
from flask import Flask, request, render_template, send_from_directory
from db.model import db, files
from npttf2utf import FontMapper, DocxHandler, TxtHandler, NoMapForOriginException, UnsupportedMapToException, TxtAutoModeException

app = Flask(__name__)

# Open the config.json file
with open("config.json", "r") as cf:
    config = json.load(cf)

logging.basicConfig(filename=config["LOGFILE"], filemode='a', level=logging.DEBUG, format='%(asctime)s, %(name)s %(levelname)s %(message)s')
app.secret_key = config["APP_SECRET_KEY"]
app.config['SQLALCHEMY_DATABASE_URI'] = config["DATABASE_URI"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create a instance of file handler classes and add file extension and its handler to dictionary
docx = DocxHandler(config["RULES_JSON"], default_unicode_font_name=config["DEFAULT_UNICODE_FONT"])
txt = TxtHandler(config["RULES_JSON"])
supportedtypes = {}
supportedtypes["docx"] = docx
supportedtypes["txt"] = txt

# Create storage directories if missing
def create_dirs():
    if not os.path.isdir(config["UPLOADED_FILES_STORAGE"]):
        logging.info("Uploaded file storage directory does not exists. Creating")
        os.makedirs(config["UPLOADED_FILES_STORAGE"])
    if not os.path.isdir(config["PROCESSED_FILES_STORAGE"]):
        logging.info("Processed file storage directory does not exists. Creating")
        os.makedirs(config["PROCESSED_FILES_STORAGE"])

# Handle user file uploads (save them in uploaded file directory and create db entry)
@app.route("/upload", methods=["POST"])
def upload():
    uploaded_file   = request.files["document"] # The uploaded file
    file_extension  = uploaded_file.filename.split(".")[-1] # split the filename by (.) and get last part somefile(.)othernamepart(.)[extension]
    random_string = ''.join(random.choice(string.ascii_letters) for x in range(32)) # Generate random string to save file in uploads directory (Orginal name will be saved in database) and it will also be set as file key to be used on other requests
    if file_extension in supportedtypes.keys() and uploaded_file.filename != "":
        try:
            uploaded_file.save(config["UPLOADED_FILES_STORAGE"]+random_string+"."+file_extension)
            autodetected_fonts = supportedtypes[file_extension].detect_used_fonts(config["UPLOADED_FILES_STORAGE"]+random_string+"."+file_extension)
            file_in_db = files(random_string, uploaded_file.filename, random_string+"."+file_extension, file_extension)
            db.session.add(file_in_db)
            db.session.commit()
            logging.info("Uploaded file was saved. Extension: %s; FileId: %s; Orginal Name: %s", file_extension, random_string,  uploaded_file.filename)
            return {"file_id": random_string, "detected_supported_fonts": autodetected_fonts, "supported_origins": supportedtypes[file_extension].supported_ttf_fonts}, 200
        except Exception as e:
            db.session.flush()
            db.session.rollback()
            logging.error("Failed to save valid file. Extension: %s; FileId: %s; Orginal Name: %s; Reason: %s", file_extension, random_string, uploaded_file.filename, str(e))
            return {"message": "Internal error. Contact administrator ! File ID: "+random_string}, 500
    else:
        logging.warning("Attempted to upload unsupported extension: %s", file_extension)
        return {"message": "No support for provided file type"}, 403

# Handle process requesst, map the font in documents using npttf2utf
@app.route("/process", methods=["POST"])
def process():
    origin_font = request.form["origin"]
    file_key = request.form["file_id"]
    file_in_db = files.query.filter(files.file_key==file_key, files.processed==False, files.uploaded_on>=int(time.time())-int(config["UPLOADS_LIFESPAN"])).first()
    if file_in_db:
        if file_in_db.ftype in supportedtypes:
            components = json.loads(request.form.get("process_components", '["body_paragraph", "table", "shape"]'))
            try:
                supportedtypes[file_in_db.ftype].map_fonts(config["UPLOADED_FILES_STORAGE"]+file_in_db.internal_name, output_file_path=config["PROCESSED_FILES_STORAGE"]+file_in_db.internal_name, from_font=origin_font, to_font="unicode", components=components)
                file_in_db.processed = True
                db.session.commit()
                logging.info("File was processed successfully. Extension: %s; FileId: %s; Orginal Name: %s", file_in_db.ftype, file_key, file_in_db.internal_name)
                return {"message": "success", "download_uri": "download/"+file_key}, 200
            except NoMapForOriginException:
                return {"message": "Unsupported font to map from"}, 500
            except UnsupportedMapToException:
                return {"message": "Cannot map to provided font/ttpeface. Unsupported !"}, 500
            except TxtAutoModeException:
                return {"message": "Font auto-convert not available for this file type"}, 500
            except Exception as e:
                logging.error("Failed to process file. Extension: %s; FileId: %s; Orginal Name: %s; Reason: %s", file_in_db.ftype, file_key, file_in_db.orginal_name, str(e))
                return {"message": "Internal error. Contact administrator with this token ("+file_key+")", "token": file_key}, 500
        else:
            logging.warning("Already uploaded file has unsupported extension. Extension: %s; FileId: %s; Orginal Name: %s", file_in_db.ftype, file_key, file_in_db.internal_name)
            return {"message": "No support for provided file type"}, 403
    else:
        logging.warning("Attempted to process nonexistent file. FileID: %s", file_key)
        return {"message": "File not found, already processsed or more than 60 minutes elapsed after upload"}, 404

# Serve the converted files
@app.route("/download/<string:file_key>", methods=["GET"])
def download(file_key):
    # Check if the file exists, is processed and file has not exceed storage lifespan
    file_in_db = files.query.filter(files.file_key==file_key, files.processed==True, files.uploaded_on>=int(time.time())-int(config["UPLOADS_LIFESPAN"])).first()
    if file_in_db:
        try:
            return send_from_directory(config["PROCESSED_FILES_STORAGE"], file_in_db.internal_name, as_attachment=True, attachment_filename=file_in_db.orginal_name)
        except Exception as e:
            logging.error("File missing. FileID: %s; Reason: %s", file_key, str(e))
            return {"message": "Critical error! File not found on server, Contact administrators with fileid. FileID: "+file_key}, 500
    else:
        logging.warning("Attempted to download nonexistent file. FileID: %s", file_key)
        return {"message": "File not found, not processsed or more than 60 minutes elapsed after upload"}, 404

# Flush all the files that have crossed their lifespan
@app.route("/flusholdfiles/<string:param_flush_key>", methods=["GET"])
def flush(param_flush_key):
    if param_flush_key == config["FLUSH_KEY"]:
        try:
            files_in_db = files.query.filter(files.uploaded_on<=int(time.time())-int(config["UPLOADS_LIFESPAN"]), files.isdeleted==False)
            for file in files_in_db:
                if os.path.exists(config["UPLOADED_FILES_STORAGE"]+file.internal_name):
                    os.remove(config["UPLOADED_FILES_STORAGE"]+file.internal_name)
                if os.path.exists(config["PROCESSED_FILES_STORAGE"]+file.internal_name):
                    os.remove(config["PROCESSED_FILES_STORAGE"]+file.internal_name)
                file.isdeleted = True
                db.session.commit()
            logging.info("Stale files flushed")
        except Exception as e:
            db.session.flush()
            logging.error("Failed to flush stale files. Reason: %s", str(e))
            return {"message": "Internal error."}, 500
    return {"message": "Done"}, 200

if __name__ == "__main__":
    create_dirs()
    with app.app_context():
        db.create_all()
    app.run(debug=bool(config["FLASK_DEBUG"]), host="0.0.0.0", port=int(config["FLASK_PORT"])) 

