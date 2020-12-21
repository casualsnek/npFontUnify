# **trippygeese**

## npttf2utf-flask
Flask Web App powered by [ttf2utf](https://github.com/trippygeese/ttf2utf) to Unify multiple Nepali ASCII font faces like Preeti, Sagarmatha, etc to Devanagari Unicode made on Python (Flask) with font autodetection and component selection. (paragraphs, table, shape/textbox)

### Features

  - Autodetects Nepali font faces used in Docx file meaning English content in the document will not be mapped to UNICODE or you can force a specific font to map every word to Unicode regardless of detected fonts
  - You can select the component whose text file will be processed in a Docx file. (shape box/shape, table, paragraphs)
  - Support for txt and Docx file
  - Web-based so no need to download anything

Free to use pre hosted public API to integrate this service into your own projects

### Installation

This tool is made in python3 so, download and install python and pip from here ( you can install from your package manager too ). 

Install the dependencies and start the server.

```
$ git clone https://github.com/trippygeese/ttf2utf-flask.git
$ cd ttf2utf-flask
$ pip install -r requirements.txt
or
$ pip3 install -r requirements.txt
$ python3 app.py
```
    
     
If everything went correctly, the application is started on the localhost on port 5000 by default. You can test by opening a web browser and opening [http://0.0.0.0:5000](http://0.0.0.0:5050).

### Configuring
- Change the FLUSH_KEY on "config.json" and set up a scheduled task to send get requests to "http://yourdomain.name/flusholdfiles/<FLUSH_KEY>" to delete old files.
- SET PORT on "config.json" to listen for connections on that port. (Default is 5000)
- Change the RULES_JSON on "config.json" to use custom mapping defination (By default mapping defination file of ttf2utf library is used).
- Change UPLOADS_LIFESPAN on "config.json" for as long as you want a file to be available for processing and downloading.
- Change UPLOADED_FILES_STORAGE and PROCESSED_FILES_STORAGE on "config.json" to use different location to save uploaded and processed files.
- Change DEFAULT_UNICODE_FONT "config.json" to set the default font for the converted document (Only for Docx file).

<br>

Supported components, supported ASCII font faces and Supported Output fonts are dependent on ttf2utf library

### **Adding support for new file type or Adding mapping for a new font**

Refer to the README.md of [ttf2utf](https://github.com/trippygeese/ttf2utf) library to add support for new font and file type. For setting up this application to accept new files types add file extension as key and instance of ttf2utf document converter and value in "supportedtypes" variable inside "app.py"

Information on endpoints are on "ENDPOINT.md"

##### Feel free to use this project for any purpose and long as you comply with the license. Any contribution to the project is highly appreciated. If you find any bugs please report it
