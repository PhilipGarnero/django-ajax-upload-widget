(function() {
    var global = this;
    var $ = global.$ || global.django.jQuery;  //  small trick for django admin
    var console = global.console || {log: function() {}};

    var AjaxUploadWidget = global.AjaxUploadWidget = function(element, options) {
        this.options = {
            selectButtonText: 'Change',
            resetButtonText: 'Remove',
            previewAreaClass: 'ajax-upload-preview',
            previewFilenameLength: 30,
            onUpload: null, // right before uploading to the server
            onComplete: null,
            onError: null,
            onRemove: null
        };
        $.extend(this.options, options);
        this.$element = $(element);
        this.initialize();
    };

    AjaxUploadWidget.prototype.DjangoAjaxUploadError = function(message) {
        this.name = 'DjangoAjaxUploadError';
        this.message = message;
    };
    AjaxUploadWidget.prototype.DjangoAjaxUploadError.prototype = new Error();
    AjaxUploadWidget.prototype.DjangoAjaxUploadError.prototype.constructor = AjaxUploadWidget.prototype.DjangoAjaxUploadError;

    AjaxUploadWidget.prototype.initialize = function() {
        var self = this;

        // Create foundation row
        this.$element.wrap('<div class="row collapse versatile"></div>');

        // Initialize preview area
        this.$previewArea = $('<div class="small-12 columns text-center '+this.options.previewAreaClass+'"></div>');
        this.$element.before(this.$previewArea);

        // Create column
        this.$element.wrap('<div class="small-6 columns versatile-url"></div>');

        // Create url field
        this.name = this.$element.attr('name');
        this.$urlElement = $('<input class="file-input-replacer compact urlinput" placeholder="Enter an url or select a file" type="url">')
        .attr('name', this.name)
        .val(this.$element.data('filename'));
        this.$element.attr('name', ''); // because we don't want to conflict with our url field
        this.$element.after(this.$urlElement);

        // Listen for when a file is selected, and perform upload
        this.$element.on('change', function(evt) {
            $(this).next('.file-input-replacer').val(this.value.replace('C:\\fakepath\\', ''));
            self.uploadFile();
        });
        this.$urlElement.on('change', function(evt) {
            self.sendUrl();
        });

        // Create select file button
        this.$selectButton = $('<div class="small-3 columns versatile-file"><a class="postfix button compact file-button-replacer">Select file</a></div>')
            .on('click', function(evt) {
                $(this).prev('.versatile-url').children('input[type="file"]').trigger('click');
            });
        this.$element.parent().after(this.$selectButton);

        // Create reset button
        this.$resetButton = $('<div class="small-3 columns versatile-reset"><a class="postfix button compact secondary">Reset file</a></div>')
            .on('click', function(evt) {
                $(this).prev('.versatile-file').prev('.versatile-url').wrap('<form>').parent('form')[0].reset();
                $(this).prev('.versatile-file').prev('form').children('.versatile-url').unwrap();
                if(self.options.onRemove) {
                    var result = self.options.onRemove.call(self);
                    if(result === false) return;
                }
                self.$urlElement.val('');
                self.displaySelection();
            });
        this.$selectButton.after(this.$resetButton);

        this.displaySelection();
    };

    AjaxUploadWidget.prototype.uploadFile = function() {
        var self = this;
        if(!this.$element.val()) return;
        if(this.options.onUpload) {
            var result = this.options.onUpload.call(this);
            if(result === false) return;
        }
        this.$element.attr('name', 'file');
        $.ajax(this.$element.data('upload-url'), {
            iframe: true,
            files: this.$element,
            processData: false,
            type: 'POST',
            dataType: 'json',
            success: function(data) { self.uploadDone(data); },
            error: function(data) { self.uploadFail(data); }
        });
    };

    AjaxUploadWidget.prototype.sendUrl = function() {
        var self = this;
        if(!this.$urlElement.val()) return;
        if(this.options.onUpload) {
            var result = this.options.onUpload.call(this);
            if(result === false) return;
        }
        this.$element.attr('name', 'file');
        $.ajax(this.$element.data('upload-url'), {
            data: {'url': this.$urlElement.val()},
            type: 'POST',
            dataType: 'json',
            success: function(data) { self.uploadDone(data); },
            error: function(data) { self.uploadFail(data); }
        });
        //Dajaxice.ajax_upload.url_download(function(data) { self.uploadDone(data); }, {'url': this.$urlElement.val()}, {'error_callback':  function(data) { self.uploadFail(data); } });
    };

    AjaxUploadWidget.prototype.uploadDone = function(data) {
        // This handles errors as well because iframe transport does not
        // distinguish between 200 response and other errors
        if(data.errors) {
            if(this.options.onError) {
                this.options.onError.call(this, data);
            } else {
                alert("The file couldn't be uploaded, try again or try reloading the page.");
                console.log(data);
            }
        } else {
            this.$urlElement.val(data.path);
            var tmp = this.$element;
            this.$element = this.$element.clone(true).val('');
            tmp.replaceWith(this.$element);
            this.displaySelection();
            if(this.options.onComplete) this.options.onComplete.call(this, data.path);
        }
    };

    AjaxUploadWidget.prototype.uploadFail = function(xhr) {
        if(this.options.onError) {
            this.options.onError.call(this);
        } else {
            alert("The file couldn't be uploaded, try again or try reloading the page.");
            console.log(xhr);
        }
    };

    AjaxUploadWidget.prototype.displaySelection = function() {
        var filename = this.$urlElement.val();

        if(filename !== '') {
            this.$previewArea.append(this.generateFilePreview(filename));
            this.$previewArea.show();
        } else {
            this.$previewArea.slideUp();
            this.$previewArea.empty();
        }
    };

    AjaxUploadWidget.prototype.generateFilePreview = function(filename) {
        output = "";
        $.each(['jpg', 'jpeg', 'png', 'gif'], function(i, ext) {
            if(filename.toLowerCase().slice(-ext.length) == ext) {
                output = '<img src="'+filename+'"/>';
                return false;
            }
        });
        return output;
    };

    AjaxUploadWidget.autoDiscover = function(options) {
        $('input[type="file"].ajax-upload').each(function(index, element) {
            new AjaxUploadWidget(element, options);
        });
    };
}).call(this);
