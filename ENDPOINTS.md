## **Endpoints:**

**Endpoint: "/upload"**

Required parameters: document* (File to convert)

Methods: POST 

EXPECTED RESPONSES:

| STATUS CODE | INFORMATION |
|--|--|
| 200  | The request was successful. Returns all supported fonts(detected_supported_fonts), fonts detected (supported_origins) and the file id (file_id) for further requests in JSON format <p> Sample response: {"detected_supported_fonts": ["Preeti", "Sagarmatha"], "file_id": "sendThisFileIdOnFurtherRequests", "supported_origins": ["Preeti", "Kantipur", "Sagarmatha"]} |
| 403 | The document format you tried to upload is unsupported. (Only .docx and .txt files are supported).<p>Sample response: {"message": "No support for provided file type"} |
| 500 | Error while processing requests. This might occur if something went wrong on the server-side or the document you uploaded is corrupted. The message filed on response gives information about the error.<p>Sample response: {"message": "Text describing the error"} |

NOTE: Parameters with * must be provided, "supported_origins" are the fonts which the server can currently map to Unicode, and "detected_supported_fonts" are the Nepali fonts which were found on your document (This field is empty in case of .txt files as autodetect won't work there)

<br>

**Endpoint: "/process"**

Required parameters: origin* (Font which is used in the document), file_id* (File id returned from the previous request on "/upload"), process_components ( Components in word document to process "body_paragraph, shape, table" can provide multiple values as json. Eg. ["body_paragraph", "table"]. Not passing this parameter will convert all supported components)

Methods: POST 

EXPECTED RESPONSES:

| STATUS CODE | INFORMATION |
|--|--|
| 200  | The request was successful and the file is converted and ready to download. The response contains the "download_uri" key containing the download link. <p> Sample response: {"message": "success", "download_uri": "download/yourFileId"} |
| 403 | You supplied unsupported font through the "origin" parameter. This will also be thrown when you try to use "auto" as origin for a .txt file.<p>Sample response: {"message": "Information about the error"} |
| 404 | The given file_id is not related to any file or the file is already processed. You can try "download/yourFileID", it will download the file if already processed or throw an error if file_id is not related to any file (File was not uploaded).<p>Sample response: {"message": "File not found, already processed or more than 60 minutes elapsed after upload"} |
| 500 | Error while processing requests. This indicates the error on server-side. Please notify me of this error, so that I can fix it.  The message filed on response gives information about the error.<p>Sample response: {"message": "Text describing the error"} |

NOTE: Parameters with * must be provided, "origin" is the font which is used on the document (It must be one of "detected_supported_fonts" returned by request on "/upload" or "auto"), if the file is .docx you can use value "auto" for origin parameter to autodetect fonts and convert them.

<br>

**Endpoint: "/download/\<YourFileId>"**

Required URI fields: YourFileId* (Your file ID which you used during the request at "/process")

Methods: GET 

EXPECTED RESPONSES:

| STATUS CODE | INFORMATION |
|--|--|
| 200  | The request was successful and the converted file will be served |
| 404 | The given file_id is not related to any file or the file is not yet processed or no request to process it was done or 60 minutes have passed since the upload of the file (We keep files only for 60 minutes). <p>Sample response: {"message": "File not found, not processed or more than 60 minutes elapsed after upload"} |
| 500 | Error while processing requests. This indicates the error on server-side. Please notify me of this error, so that I can fix it.  The message filed on response gives information about the error.<p>Sample response: {"message": "Text describing the error"} |

<br>

**Endpoint: "/flusholdfiles/\<FLUSH_KEY>"**

Required URI fields: FLUSH_KEY* (The flush key you set in config.json)

Methods: GET 

EXPECTED RESPONSES:

| STATUS CODE | INFORMATION |
|--|--|
| 200  | The request was successful and old files were flushed (Maybe).  |
| 500 | Error while processing requests. This indicates the error on server-side. Please notify me of this error, so that I can fix it.  The message filed on response gives information about the error.<p>Sample response: {"message": "Text describing the error"} |

NOTE: This endpoint return status code 200 even if flush was not done due to wrong flush_key. Refer to logfile to know if files were actually flushed