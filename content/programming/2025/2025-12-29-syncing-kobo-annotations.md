---
title: "Syncing Kobo Annotations"
date: 2025-12-29
programming/topics: []
draft: True
---
I've recently been trying out a [Kobo](https://www.kobo.com/). Amazon has some issues and Kindles are hard to do any amount of customization to, let's just leave it at that. 

So what fun tricks can one do with a Kobo? 

Well, for one, it's a Linux system. And if you attach it to your computer, you get access to a lot of the local filesystem. This includes the SQLite database holding all of teh system metadata, along with places to install all sorts of interesting scripts. 

One that I've been wanting in particular is the ability to extract my annotations. It's a great way to [review](/reviews) books. Highlight, write a note, and then export right at the end. 

So how do you do that on a Kobo? 

{{<toc>}}

- - -

<!--more-->

## Starting point

Well, to start out, I found [this thread](https://www.mobileread.com/forums/showthread.php?t=349637). This gives me the initial script, although it's designed to extract the notes directly on device. I wanted more control than that. 

## Via Dropbox

So here we end up with this script:

```bash
#!/bin/sh

APP_KEY="..."
APP_SECRET="..."
REFRESH_TOKEN="..."

NOTES="/mnt/onboard/.adds/notes"

DB="/mnt/onboard/.kobo/KoboReader.sqlite"
CURL="${NOTES}/curl"
CERT="${NOTES}/ca-bundle.crt"

LD_LIBRARY_PATH="${NOTES}/lib:${LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH

# First we need a short lived access token
ACCESS_TOKEN=$($CURL --cacert $CERT -s -X POST https://api.dropboxapi.com/oauth2/token \
  -u "$APP_KEY:$APP_SECRET" \
  -d grant_type=refresh_token \
  -d refresh_token="$REFRESH_TOKEN" \
  | grep -o '"access_token": *"[^"]*"' \
  | sed 's/.*: *"//;s/"$//')

# Then we can actually upload the file
$CURL --cacert $CERT -X POST https://content.dropboxapi.com/2/files/upload \
    --header "Authorization: Bearer $ACCESS_TOKEN" \
    --header "Dropbox-API-Arg: {\"path\": \"/KoboReader.sqlite\",\"mode\": \"overwrite\",\"mute\": false}" \
    --header "Content-Type: application/octet-stream" \
    --data-binary @"$DB"
```

This is ... slightly odd. Since we're bundling `curl` and the `ca-bundle.crt` directly rather than installing them on the system. Other than that, we'll be using the Dropbox API in three parts:

1. Go to https://www.dropbox.com/developers/apps
2. Click “Create app”
   1. Scoped access
   2. Select App Folder
   3. Scopes: `files.content.write` and `files.content.read`
   4. Save the app key and secret
3. Get your refresh token
   1. Visit `https://www.dropbox.com/oauth2/authorize?client_id=APP_KEY&response_type=code&token_access_type=offline`
   2. Copy the code from the 'access code generated' page
4. Create a refresh token:

  ```bash
  curl -X POST https://api.dropboxapi.com/oauth2/token \
    -u YOUR_APP_KEY:YOUR_APP_SECRET \
    -d code=ACCESS_CODE \
    -d grant_type=authorization_code
  ```

After that is all set up, we need a way to run it:

## Adding a button on the Kobo

As I mentioned, use NickleMenu to add a button:

```text
menu_item :main :Send DB :nickel_wifi :autoconnect
  chain_success :cmd_spawn :quiet :/mnt/onboard/.adds/notes/send-db.sh
  chain_success :dbg_toast :Syncing Notes
```

Now, unmount, restart, and click the new 'Send DB' button. 

Voilá. We have the kobo database in our Dropbox!

## Exporting notes

Okay, for the next part, I took the SQL queries from the original forum thread, wrapped them in some Python, and used that to export them:

```python
import os
import re
import sqlite3
import datetime

db = sqlite3.connect("KoboReader.sqlite")
db.row_factory = sqlite3.Row

query = """
SELECT 
    c.Title as title,
    COALESCE(c_chapter_titled.Title, c_chapter.Title, b.ContentID) as chapter,
    b.Text as text,
    b.Annotation as annotation
FROM 
    Bookmark b
    INNER JOIN content c ON b.VolumeID = c.ContentID
    LEFT JOIN content c_chapter_titled ON c_chapter_titled.ContentID = b.ContentID || '-1'
    LEFT JOIN content c_chapter ON c_chapter.ContentID = b.ContentID
ORDER BY 
    c.Title ASC,
    CAST(COALESCE(SUBSTR(b.ContentID, INSTR(b.ContentID, 'chapter_') + 8, 3), '0') AS INTEGER) ASC,
    b.ChapterProgress ASC,
    b.DateCreated ASC
"""

os.makedirs("notes", exist_ok=True)

buffer = ""
last_title = None
last_chapter = None


def write_out():
    """Write the buffer to a file and clear it (if it's not empty)"""

    global buffer, last_title, last_chapter

    if buffer:
        path = os.path.join("notes", last_title + ".md")

        print(f"Writing {path}")
        with open(path, "w") as f:
            f.write(buffer)

        buffer = ""
        last_chapter = None


def markdownify(text):
    """Convert text to a markdown blockquote"""

    # Add markdown blockquotes (with paragraphs)
    text = re.sub(r"^\s*(.*)", r"> \1\n> ", text, flags=re.MULTILINE)

    # Remove multiple empty lines within blockquotes
    text = re.sub(r"(^>\s*$\n?){2,}", ">\n", text, flags=re.MULTILINE)

    # Remove trailing empty lines of blockquotes
    text = re.sub(r"^>\s*$(^$){2,}", "", text, flags=re.MULTILINE)

    return text


for title, chapter, text, annotation in db.execute(query):
    # Skip bookmarks
    if not text:
        continue

    # If we've switched books, print the new one
    if title != last_title:
        print(f"New title: {title}")
        write_out()
        buffer += f"# {title}\n\n"
        last_title = title

    # Likewise, chapters
    chapter = chapter.split("#")[-1]
    if chapter != last_chapter:
        print(f"New chapter: {chapter}")
        buffer += f"## {chapter}\n\n"
        last_chapter = chapter

    # TODO: Format as markdown
    buffer += markdownify(text) + "\n\n"

    if annotation:
        buffer += annotation + "\n\n"

write_out()

db_time = os.path.getmtime("KoboReader.sqlite")
db_time = datetime.datetime.fromtimestamp(db_time)

my_time = datetime.datetime.now()

print()
print(f"Database last modified: {db_time}")
print(f"Time since last modified: {my_time - db_time}")
```

Converting to Markdown and cleaning up the markdown took a moment. 

Other than that, we now have a number of Markdown files--one for each book, with each highlights (and optionally note text), broken down by chapter. 

It doesn't work for every book (it depends on how the epub is laid out), but it does mostly work. 

## Todo

So what can I do next? As easy as it makes things, I'd actually like to remove the dependency on Dropbox and directly build a server into the Python script. That will catch the DB, automatically generate the Markdown, and allow me to look at it in a browser. Easy enough if it's living on my local network (perhaps with a [[DNS/Wireguard Tunnel Weirdness on iOS|wireguard]]() tunnel). But for now, this works fine. 

Onward!