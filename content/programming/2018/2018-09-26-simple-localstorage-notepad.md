---
title: Simple LocalStorage Notepad
date: 2018-09-26
programming/languages:
- HTML
- JavaScript
---
I have a large number of keyword bookmarks in whichever browser I happen to be using at the time that I've been building up over the years[^todo]. One of the ones I particular enjoy is `text`: `data:text/html, <html contenteditable>`. What that does is open a new tab where I can take notes, completely locally. It's really handy... but there's one big problem: I often accidentally close the tab and lose whatever I had been typing. So I decided to take a few minutes to write up a simple extension of the idea that would save the data to [[wiki:LocalStorage]]().

<!--more-->

Long story short, most of the content comes from the JavaScript:

```javascript
(function() {
    var editorKey = 'html5-notepad';
    var editor = document.getElementById('editor');
    var cache = localStorage.getItem(editorKey);

    if (cache) {
        editor.innerHTML = cache;
    }

    function autosave() {
        var newValue = editor.innerHTML;
        if (cache != newValue) {
            cache = newValue;
            localStorage.setItem(editorKey, cache);
        }
    }

    editor.addEventListener('input', autosave);
})();
```

It's hopefully fairly straight forward. We set up an `autosave` function that will take whatever has been typed in the `editor` `div` (we'll create this in a moment) and shoves it into `localStorage`, then bind that to the `input` event listener. We could have used `editor.onchange`, but only if we were using a `textarea`, since only input elements have that method. That took a bit to debug.

Another option would be just to save periodically (`setInterval(autosave, 250);`), but that would keep saving over and over again even when I'm not using the notepad, which I didn't want.

And then finally, we automatically load the value when the page is loaded (making sure there was actually a value set).

Next up, the HTML and a bit of CSS to make it look nicer:

```html
<html>
<head>
    <meta charset="utf-8">
    <title>html5-notepad</title>

    <style>
#editor {
    width: 100%;
    height: 100%;
}
    </style>
</head>
<body>
    <div id="editor" contenteditable="true"></div>
</body>
<script>
...
</script>
</html>

```

And, that's about it. There's one major downside of this over the initial approach is that you cannot embed it in a `data:` frame to run without a server, since `localStorage` isn't accessible in `data:` frames (for perfectly reasonable security reasons). That's not a super big deal though. The impact is minimal enough, I don't mind hosting it. Heck, here's a copy:

<iframe style="width: 100%; height: 200px;" src="/embeds/2018/localstorage-notepad.html"></iframe>

Anything you type in that box will be accessible if you close the page, go away, and come back later. And it's never sent to my servers or stored anywhere other than in your browser. Pretty cool, no?

[^todo]: I should write that up at some point...
