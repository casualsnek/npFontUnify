var document_id = "";
$(document).ready(function () {
    $(".document-upload").on("change", function (event) {
        if ($(".document-upload").val().endsWith(".docx") || $(".document-upload").val().endsWith(".txt")) {
            if ($(".document-upload").val().endsWith(".docx")) {
                $(".process_components").prop('disabled', false);
            }
            else if ($(".document-upload").val().endsWith(".txt")) {
                $(".process_components").prop('disabled', true);
            }
            var data = new FormData();
            data.append("document", document.getElementById("document-upload").files[0]);
            $(".wait-notice").show();
            $(".document-upload-card").hide();
            $.ajax({
                type: "POST",
                enctype: "multipart/form-data",
                url: "/upload",
                data: data,
                processData: false,
                contentType: false,
                cache: false,
                timeout: 800000,
                dataType: "json",
                success: function (data) {
                    document_id = data.file_id;
                    $(".origin-selection").html("");
                    $(".target-selection").html("");
                    console.log("SUCCESS : ", data);
                    if (data.detected_supported_fonts.length > 0) {
                        var all_detected_fonts = "";
                        for (i = 0; i < data.detected_supported_fonts.length; i++) {
                            all_detected_fonts = all_detected_fonts + data.detected_supported_fonts[i];
                            if (i != data.detected_supported_fonts.length - 1) {
                                all_detected_fonts = all_detected_fonts + ", ";
                            }
                        }
                        $(".origin-selection").append(
                            '<input type="radio" name="origin-map" id="auto" class="origin-map" value="auto" checked="checked"><label for="auto">&nbsp;&nbsp;Autodetect (' + all_detected_fonts + ")</label><br>"
                            );
                    }
                    for (i = 0; i < data.supported_origins.length; i++) {
                        $(".origin-selection").append(
                            '<input type="radio" name="origin-map" id="' +
                            data.supported_origins[i] +
                            '" class="origin-map" value="' +
                            data.supported_origins[i] +
                            '"><label for="auto">&nbsp;&nbsp;' +
                            data.supported_origins[i] +
                            "</label><br>"
                            );
                    }
                    for (i = 0; i < data.supported_targets.length; i++) {
                        $(".target-selection").append(
                            '<input type="radio" name="target-map" id="' +
                            data.supported_targets[i] +
                            '" class="target-map" value="' +
                            data.supported_targets[i] +
                            '"><label for="auto">&nbsp;&nbsp;' +
                            data.supported_targets[i] +
                            "</label><br>"
                            );
                    }

                    $(".wait-notice").hide();
                    $(".font-selection-card").show();
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    var response = jQuery.parseJSON(jqXHR.responseText);
                    $(".wait-notice").hide();
                    $(".document-upload-card").show();
                    $("#modal-notice-text").html(response.message);
                    $("#modal-notice-image").attr("src", "static/assets/error.svg");
                    $(".modal-notice").modal("show");
                },
            });
        } else {
            $("#modal-notice-text").html("Only .docx (Wicrosoft word document or .txt (plaintext) files are supported !");
            $("#modal-notice-image").attr("src", "static/assets/error.svg");
            $(".modal-notice").modal("show");
        }
    });
    $("#processdocument").on("click", function (event) {
        if (document_id != "" && typeof $(".origin-map:checked").val() != "undefined" && typeof $(".target-map:checked").val() != "undefined") {
            var formdata = { origin: $(".origin-map:checked").val(), target: $(".target-map:checked").val(), file_id: document_id, process_components: "" };
            var components = []
            $(".process_components:checked").each(function() {
                components.push($(this).val());
                console.log($(this).val())
            });
            formdata.process_components = JSON.stringify(components)
            $(".font-selection-card").hide();
            $(".wait-notice").show();
            $.ajax({
                type: "POST",
                url: "/process",
                data: formdata,
                timeout: 800000,
                dataType: "json",
                success: function (data) {
                    $("#filedownloadlink").attr("href", "/" + data.download_uri);
                    $(".wait-notice").hide();
                    $(".document-download-card").show();
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    var response = jQuery.parseJSON(jqXHR.responseText);
                    $(".wait-notice").hide();
                    $(".font-selection-card").show();
                    $("#modal-notice-text").html(response.message);
                    $("#modal-notice-image").attr("src", "static/assets/error.svg");
                    $(".modal-notice").modal("show");
                },
            });
        } else {
            console.log("No origin font selected");
        }
    });
    $("#switchtofile").on("click", function (event) {
        $(".card-type-mode").hide();
        $(".card-document-mode").show();
    });
    $("#switchtolive").on("click", function (event) {
        $(".card-document-mode").hide();
        $(".card-type-mode").show();
    });

    $('#live-text').keypress(function(event){
        var keycode = (event.keyCode ? event.keyCode : event.which);
        console.log(keycode)
        if(keycode == '32'){
            var formdata = { origin: $("#live-origin").find(":selected").text(), target: $("#live-target").find(":selected").text(), text: $("#live-text").val()+" " };
            console.log(formdata)
            $.ajax({
                type: "POST",
                url: "/processtext",
                data: formdata,
                timeout: 800000,
                dataType: "json",
                success: function (data) {
                    console.log(data)
                    $("#live-text").val(data.text);
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    var response = jQuery.parseJSON(jqXHR.responseText);
                    console.log(response.message)
                },
            });
        }
    });
});