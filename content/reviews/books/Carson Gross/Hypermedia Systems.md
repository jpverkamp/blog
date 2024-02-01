---
cover: /embeds/books/hypermedia-systems.jpg
date: '2024-01-27'
goodreads_id: 192405005
rating: 4
reviews/authors:
- Carson Gross
reviews/lists:
- 2024 Book Reviews
title: Hypermedia Systems
---
HTMX. HTML, but better*!

```html
<button hx-delete="/contacts/{{ contact.id }}"
        hx-push-url="true"
        hx-confirm="Are you sure you want to delete this contact?" (1)
        hx-target="body">
Delete Contact
</button>
```

Basically, the entire idea is that you don't need quite so much (explicit) JavaScript everywhere. It should be possible to declaratively design pages that can automatically take actions (including HTTP verbs other than `GET` and `POST`) and replace (partial) content on pages. 

That's why I read the book.

<!--more-->

Underlying this idea is the more general new/old idea of Hypermedia. What the web 'could have been'. Linked content, basically like digital books (albeit more choose-your-own-adventurey). And that's what HTMX strives to be!

I really like the idea and--although it gets almost preach at times--fully intend to try build / rebuild my sites with these ideas. JavaScript is awesome. But it would be better if it weren't (directly) needed for so much! (Blasphemy I know). 

And then we get into the mobile side. Where instead of using HTMX, they have their entirely custom XML based hypermedia system. Feels weird. Perhaps I'm just not enough mobile dev to go for it. But perhaps it's worth a try after all. 

We shall see. 

I enjoyed the book. But it's a niche topic among niche topics, so YMMV. 
