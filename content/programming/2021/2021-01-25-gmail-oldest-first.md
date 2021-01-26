---
title: GMail Oldest First
date: 2021-01-25
programming/languages:
- JavaScript
programming/topics:
- Email
- Gmail
- Userscripts
---
It's been [rather a while]({{< ref "2016-01-02-inlining-plaintext-attachments-in-gmail.md" >}}) since I last worked on a userscript, but there's been a problem I've been trying to solve for some time. 

I want to have my GMail in order from oldest to newest. While you can do this for all messages, you can't do it within a single page. 

<!--more-->

My original idea was to use a script that would make a button you could click to reverse the order: [https://github.com/jpverkamp/userscripts/blob/master/gmail-reverse-order-button.user.js](gmail-reverse-order-button.user.js). It would find the `li` elements that contained the messages and literally reverse those HTML elements. Visually, it worked great! But unfortunately, it didn't work. When you clicked a message, it opened the one that should have been there, not the one that way. 

Sadness.

This time around though, I cheated. I didn't re-order the elements at all. Instead, I used the power of CSS to tell the browser to play them backwards:

```css
table.F.cf.zt tbody {
    display: flex;
    flex-direction: column-reverse;
}   
```

The classes `.F.cf.zt` are because Google obfuscates their classes and IDs, both to save on space (a reasonable problem at that scale) but also to prevent exactly this sort of thing from working. But for the moment, it's relatively stable.

With that, the only step left is to add that style to the page with [TamperMonkey](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/) (although if you're using Chrome, you can install it directly):

```javascript
(function() {
    let head = document.getElementsByTagName('head')[0];
    let style = document.createElement('style');
    style.type = 'text/css';
    style.innerHTML = `
table.F.cf.zt tbody {
    display: flex;
    flex-direction: column-reverse;
}    
    `;
    head.appendChild(style);
    console.log('GMail Oldest First applied style');
})();
```

Really, that's it. 

If you'd like to install it, you can do so here: [https://github.com/jpverkamp/userscripts/raw/master/gmail-oldest-first.user.js](gmail-oldest-first.user.js)