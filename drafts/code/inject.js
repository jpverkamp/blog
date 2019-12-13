// ==UserScript==
// @name       xss-all-the-things
// @namespace  https://blog.jverkamp.com
// @version    0.1
// @match      file://*/*
// @match      http://*/*
// @match      https://*/*
// @match      localhost
// @require    http://code.jquery.com/jquery-latest.js
// @copyright  2014+, JP Verkamp
// ==/UserScript==

$(function() {
    // Given an element or jQuery selector, create a path unique to that element
    // Trace back through the entire DOM to the root, for each node:
    // - Include the tag
    // - If the node has an ID, include that
    // - If not and it has classes, include those
    // - If there are siblings with the same tag and classes, add an index
    var getPath = function(el) {
        var $el = $(el);

        return '//' +  $el.parents().andSelf().map(function(_, el) {
            $el = $(el);

            var node = el.nodeName;

            if ($el.attr('id')) {
                node += '#' + $el.attr('id');
            } else if ($el.attr('class')) {
                var classes = '.' + $el.attr('class').replace(new RegExp(' ', 'g'), '.');
                node += classes;

                var sameSiblings = $el.parent().find(classes);
                if (sameSiblings.length > 1) {
                    node += '[' + sameSiblings.index(el) + ']';
                }
            } else {
                var siblings = $el.parent().find(el.nodeName);
                if (siblings.length > 1) {
                    node += '[' + siblings.index(el) + ']';
                }
            }

            return node;
        }).get().join('/');
    };

    // Given an element, inject it's path (see above) as it's value
    // Wrap this in exception handling, mostly because of file inputs
    var inject = function(_, el) {
        try {
            var path = getPath(el);
            var attack = '"><img src=x onerror=alert(\'' + path + '\')';
            $(el).val(attack);
        } catch(ex) {
            console.log('failed to inject:');
            console.log(el);
            console.log(ex);
        }
    };

    // Intentionally global
    // Add XSS tags to common input type objects
    xssAllTheThings = function() {
        $('button').each(inject);
        $('input:not([type="file"])').each(inject);
        $('textarea').each(inject);
        $('option').each(inject);
    };

    // Create a button on the bottom right of the browser to run XSS injection
    var $runButton = $('<div>')
        .html('<a href="#">XSS ALL THE THINGS</a>')
        .css('position', 'fixed')
        .css('bottom', '0px')
        .css('right', '0px')
        .css('background', 'white')
        .css('border', '1px solid black')
        .css('padding', '0.5em')
        .css('margin', '0.5em')
        .css('border-radius', '0.5em')
        .click(xssAllTheThings);

    // Add the run button to the page
    $('body').append($runButton);
});
