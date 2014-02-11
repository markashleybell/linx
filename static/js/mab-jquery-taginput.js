/*!
 * jQuery lightweight plugin boilerplate
 * Original author: @ajpiano
 * Further changes, comments: @addyosmani
 * Licensed under the MIT license
 */

// the semi-colon before the function invocation is a safety
// net against concatenated scripts and/or other plugins
// that are not closed properly.
;(function ( $, window, document, undefined ) {

    // undefined is used here as the undefined global
    // variable in ECMAScript 3 and is mutable (i.e. it can
    // be changed by someone else). undefined isn't really
    // being passed in so we can ensure that its value is
    // truly undefined. In ES5, undefined can no longer be
    // modified.

    // window and document are passed through as local
    // variables rather than as globals, because this (slightly)
    // quickens the resolution process and can be more
    // efficiently minified (especially when both are
    // regularly referenced in your plugin).

    // Create the defaults once
    var pluginName = "tagInput",
        defaults = {
            typeahead: false,
            typeaheadOptions: {}
        },
        KEYCODES = {
            ENTER: 13,
            TAB: 9,
            BACKSPACE: 8
        };

    // The actual plugin constructor
    function Plugin(element, options) {
        this.element = element;

        // jQuery has an extend method that merges the
        // contents of two or more objects, storing the
        // result in the first object. The first object
        // is generally empty because we don't want to alter
        // the default options for future instances of the plugin
        this.options = $.extend({}, defaults, options) ;

        this._defaults = defaults;
        this._name = pluginName;

        this.init();
    }

    var cleanArray = function(arr, deleteValue) {
        if(typeof deleteValue === 'undefined')
            deleteValue = '';

        for (var i = 0; i < arr.length; i++) {
            if (arr[i] == deleteValue) {         
                arr.splice(i, 1);
                i--;
            }
        }

        return arr;
    };

    var createTagInput = function(input) {
        var tags = cleanArray(input.val().split('|'));
        var tagLabels = $.map(tags, function(item, index) {
            return '<span class="label label-primary">' + item + ' <span class="glyphicon glyphicon-remove"></span></span>';
        }).join('');

        return $('<div class="mab-jquery-taginput' + ((input.attr('class')) ? ' ' + input.attr('class') : '') + '">' + 
                 tagLabels + 
                 '<input class="mab-jquery-taginput-data" type="hidden" name="' + input.attr('name') + '" id="' + input.attr('name') + '" value="' + input.val() + '">' +
                 '<input class="mab-jquery-taginput-input" type="text">' + 
                 '</div>');
    };

    Plugin.prototype = {

        init: function() {
            // Place initialization logic here
            // You already have access to the DOM element and
            // the options via the instance, e.g. this.element
            // and this.options
            // you can add more functions like the one below and
            // call them like so: this.yourOtherFunction(this.element, this.options).
            var input = $(this.element);
            var tagInput = createTagInput(input);
            input.replaceWith(tagInput);

            var typeaheadInput = tagInput.find('.mab-jquery-taginput-input');

            if(this.options.typeahead) {
                typeaheadInput.typeahead(null, this.options.typeaheadOptions);
            }
                
            var typeaheadData = tagInput.find('.mab-jquery-taginput-data');

            typeaheadInput.on('keypress', function(e) {

                var input = $(this);

                if(e.keyCode == KEYCODES.ENTER) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            });

            typeaheadInput.on('keydown', function(e) {
                
                var input = $(this);

                if(e.keyCode == KEYCODES.ENTER && $.trim(input.val()) !== '') {
                    typeaheadData.before('<span class="label label-primary">' + input.val() + ' <span class="glyphicon glyphicon-remove"></span></span>');
                    typeaheadData.val(typeaheadData.val() + '|' + input.val());
                    input.typeahead('val', '');
                    input.typeahead('close');
                }

                if(e.keyCode == KEYCODES.TAB) {
                }

                if(e.keyCode == KEYCODES.BACKSPACE) {
                    typeaheadData.prev('span.label').remove();
                    typeaheadData.val(typeaheadData.val().split('|').slice(0, -1).join('|'));
                    input.typeahead('val', '');
                    input.typeahead('close');
                }
            });
        }

        // yourOtherFunction: function(el, options) {
        //     // some logic
        // }
    };

    // A really lightweight plugin wrapper around the constructor,
    // preventing against multiple instantiations
    $.fn[pluginName] = function (options) {
        return this.each(function() {
            if (!$.data(this, "plugin_" + pluginName)) {
                $.data(this, "plugin_" + pluginName,
                new Plugin(this, options));
            }
        });
    };

})(jQuery, window, document);