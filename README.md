# **trippygeese**

## npFontUnify
Flask Web App powered by [npttf2utf](https://github.com/trippygeese/npttf2utf) to Unify multiple Nepali ASCII font faces like Preeti, Sagarmatha, etc to Devanagari Unicode or Preeti made on Python (Flask) with font autodetection and component selection. (paragraphs, table, shape/textbox)

[Demo Website ](https://npfontunify.herokuapp.com/)

__Website may not be online__


### Features

  - Autodetect Nepali font faces used in Docx file meaning English content in the document will not be mapped to unicode, or you can force a specific font to map every word to Unicode regardless of detected fonts
  - You can select the component whose text file will be processed in a Docx file. (shape box/shape, table, paragraphs)
  - Support for txt and Docx file
  - Web-based so no need to download anything
  - Live origin to target font mapping (similar to what most sites feature)

### Installation

This tool is made in python3 so, download and install python and pip from here ( you can install from your package manager too ). 

Install the dependencies and start the server.

```
$ git clone https://github.com/trippygeese/npFontUnify.git
$ cd npttf2utf-flask
$ pip install -r requirements.txt
or
$ pip3 install -r requirements.txt
$ python3 app.py
```
    
     
If everything went correctly, the application is started on the localhost on port 5000 by default. You can test by opening a web browser and opening [http://0.0.0.0:5000](http://0.0.0.0:5050).

### Configuring
Configuration of application is done using environment variable. The environment variables and information about them are presented in table below

| Environment Variable  | Description  | Default value |
| ------------ |---------------| -----|
| RULES_JSON      | Rule file used for mapping fonts to unicode | Default 'map.json' file from directory of imported 'npttf2utf' library|
| FLUSH_KEY      | Phrase to be passed to ``` /flush_files/<UPLOADS_LIFESPAN> ``` which flushes old files in server         |   ___Random___ |
| SECRET KEY      | Secret key for flask |   ___Random___ |
| UPLOADS_LIFESPAN | Max time for which an uploaded or processed file is marked as processable or downloadable. (In minutes) Files which exceeds this period of time are deleted when ```/flush_files/<UPLOADS_LIFESPAN>``` is requested with correct UPLOADS_LIFESPAN       | 3600 |
| DEFAULT_UNICODE_FONT   | Default font face set for text converted to unicode (Only for docx files)  | Kalimati  |
| UPLOADED_FILES_STORAGE | Location where user uploaded files are stored | ```<app.py's location>/user_files/uploads/``` |
| PROCESSED_FILES_STORAGE | Location where user processed files are stored | ```<app.py's location>/user_files/processed/``` |
| HOST | Host on which flask listens for connections | 0.0.0.0 |
| POST | Port on which flask listens for connections | 500 |

Supported components, supported ASCII font faces and Supported Output fonts are dependent on npttf2utf library


## **Endpoints:**

**Endpoint: "/upload"**

Required parameters: 
 - **document*** (File to convert)

Methods: POST 

EXPECTED RESPONSES:

| STATUS CODE | INFORMATION |
|--- |--|
| 200  | The request was successful. Returns all supported fonts(detected_supported_fonts), fonts detected (supported_origins) and the file id (file_id) for further requests in JSON format <p> Sample response: {"detected_supported_fonts": ["Preeti", "Sagarmatha"], "file_id": "sendThisFileIdOnFurtherRequests", "supported_origins": ["Preeti", "Kantipur", "Sagarmatha"]} |
| 403 | The document format you tried to upload is unsupported. (Only .docx and .txt files are supported).<p>Sample response: {"message": "No support for provided file type"} |
| 500 | Error while processing requests. This might occur if something went wrong on the server-side or the document you uploaded is corrupted. The message filed on response gives information about the error.<p>Sample response: {"message": "Text describing the error"} |


NOTE: Parameters with * must be provided, "supported_origins" are the fonts which the server can currently map to Unicode, and "detected_supported_fonts" are the Nepali fonts which were found on your document (This field is empty in case of .txt files as autodetect won't work there)


**Endpoint: "/process"**

Required parameters: 
- **origin*** (Font which is used in the document)
- **target*** (Target font to which file will be mapped to)
- **file_id*** (File id returned from the previous request on "/upload")
- **process_components** ( Components in word document to process "body_paragraph, shape, table" can provide multiple values as json. Eg. ["body_paragraph", "table"]. Not passing this parameter will convert all supported components)

Methods: POST 

EXPECTED RESPONSES:

| STATUS CODE | INFORMATION |
|--|--|
| 200  | The request was successful, and the file is converted and ready to download. The response contains the "download_uri" key containing the download link. <p> Sample response: {"message": "success", "download_uri": "download/yourFileId"} |
| 403 | You supplied unsupported font through the "origin" parameter. This will also be thrown when you try to use "auto" as origin for a .txt file.<p>Sample response: {"message": "Information about the error"} |
| 404 | The given file_id is not related to any file, or the file is already processed. You can try "download/yourFileID", it will download the file if already processed or throw an error if file_id is not related to any file (File was not uploaded).<p>Sample response: {"message": "File not found, already processed or more than 60 minutes elapsed after upload"} |
| 500 | Error while processing requests. This indicates the error on server-side. Please notify me of this error, so that I can fix it.  The message filed on response gives information about the error.<p>Sample response: {"message": "Text describing the error"} |

NOTE: Parameters with * must be provided, "origin" is the font which is used on the document (It must be one of "detected_supported_fonts" returned by request on "/upload" or "auto"), if the file is .docx you can use value "auto" for origin parameter to autodetect fonts and convert them.


**Endpoint: "/download/\<YourFileId>"**

Required URI fields: 
- **YourFileId*** (Your file ID which you used during the request at "/process")

Methods: GET 

EXPECTED RESPONSES:

| STATUS CODE | INFORMATION |
|--|--|
| 200  | The request was successful, and the converted file will be served |
| 404 | The given file_id is not related to any file, or the file is not yet processed or no request to process it was done or 60 minutes have passed since the upload of the file (We keep files only for 60 minutes). <p>Sample response: {"message": "File not found, not processed or more than 60 minutes elapsed after upload"} |
| 500 | Error while processing requests. This indicates the error on server-side. Please notify me of this error, so that I can fix it.  The message filed on response gives information about the error.<p>Sample response: {"message": "Text describing the error"} |


**Endpoint: "/flush_files/\<FLUSH_KEY>"**

Required URI fields: 
- **FLUSH_KEY*** (The flush key you set in config.json)

Methods: GET 

EXPECTED RESPONSES:

| STATUS CODE | INFORMATION |
|--|--|
| 200  | The request was successful and old files were flushed (Maybe).  |
| 500 | Error while processing requests. This indicates the error on server-side. Please notify me of this error, so that I can fix it.  The message filed on response gives information about the error.<p>Sample response: {"message": "Text describing the error"} |

NOTE: This endpoint return status code 200 even if flush was not done due to wrong flush_key. Refer to logfile to know if files were actually flushed


**Endpoint: "/processtext"**

Required parameters: 
- **origin** (Font which is used in the text)
- **target** (Target font to which text will be mapped to)
- **text*** (The text which is to be mapped)

Methods: POST, GET

EXPECTED RESPONSES:

| STATUS CODE | INFORMATION |
|--|--|
| 200  | } |
| 403 | The origin or target you provided is not available/supported. Reason will be on "message" key of response JSON} |
| 500 | Error while processing requests. This indicates the error on server-side. |

NOTE: Parameters with * must be provided, "origin" is the font on which text is typed (It must be one of supported origin of npttf2utf library used).

### **Adding support for new file type or Adding mapping for a new font**

Refer to the 'README.md' of [npttf2utf](https://github.com/trippygeese/npttf2utf) library to add support for new font and file type. For setting up this application to accept new files types add file extension as key and instance of npttf2utf document converter and value in "supported_types" variable inside "app.py"

##### Feel free to use this project for any purpose and long as you comply with the license. Any contribution to the project is highly appreciated. If you find any bugs please report it
