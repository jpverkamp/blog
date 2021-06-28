---
title: Generating a Book Bingo Chart in Hugo
date: 2021-06-26
programming/languages:
- Go
programming/sources:
- APIs
- Hugo
---
Another [r/Fantasy 2021 Book Bingo]({{< ref "2021-04-01-book-bingo" >}}) post! How in the world am I generating this (updating) chart in Hugo?

{{< bingo "2021 Book Bingo" >}}

<!--more-->

To start, I have a [Data file](https://gohugo.io/templates/data-templates/) for the names of the categories:

```yaml
- 
  - "SFF anthology or collection"
  - "Set in Asia (Hard: by an Asian author)"
  ...
- 
  - "r/Fantasy Book Club (Hard: with participation)"
  ...
...
```

It's just markdown (for links) in a nested list. 5x5 (hard coded) at the moment, but I could probably make that flexible if I wanted. 

Next, I have to add a bit of metadata to each post that's going to be included in a Book Bingo:

```yaml
bingo:
- 2021 Book Bingo
bingo-data:
    2021 Book Bingo: [3x1+]
```

It's a bit annoying that I have to do this. What I'd really want is for the Taxonomy to support a hash as the data field, so I could just do:

```yaml
bingo:
    2021 Book Bingo: [3x1+]
```

But if you do that, the post isn't included in the `bingo` taxonomy. So I have to include both. If I figure out a better way to do that, I'll update this post, but for the moment, it's okay. So `bingo` is a [Taxonomy](https://gohugo.io/content-management/taxonomies/) (so I can list all pages that match it without cycling through all pages), while `bingo-data` is just a `$Page.Param` that I can access. The field is: `{row}x{column}{hard mode flag}`. 

Finally, I actually make a shortcode that can use that information and build a table:

{{< source "hugo" "source.hugo" >}}

- `range` over the rows and columns, building an HTML table
- In each cell:
    - Include the title of the cell from the data page
    - Build a `index` (and `indexHard`) for that row and column
    - Search over all pages in the matching Taxonomy, use the Page Data to see if they match this specific `index` or not
    - If so, include the cover as a link, plus the '(Hard Mode)' flag

I'll admit, it feels a bit hacky, but one of the beautiful things about a static site generator is that it only has to run when rebuilding my site. The end result is just HTML. And I only have to update the individual pages, not keep a central list. I think that's pretty neat. 

Perhaps I should figure out more things I can do with Page Data. Perhaps keep track of authors as well as series? Ratings? Who knows!