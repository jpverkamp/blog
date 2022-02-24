---
title: A simple Flask Logging/Echo Server
date: 2022-02-01
programming/languages:
- Python
programming/sources:
- Small Scripts
programming/topics:
- Flask
- Web Development
- Security
- HTTP
- JSON
---
A very simple server that can be used to catch all incoming HTTP requests and just echo them back + log their contents. I needed it to test what a webhook actually returned to me, but I'm sure that there are a number of other things it could be dropped in for. 

It will take in any GET/POST/PATCH/DELETE HTTP request with any path/params/data (optionally JSON), pack that data into a JSON object, and both log that to a file (with a UUID1 based name) plus return this object to the request. 

Warning: Off hand, there is already a potential security problem in this regarding DoS. It will happily try to log anything you throw at it, no matter how big and will store those in memory first. So long running requests / large requests / many requests will quickly eat up your RAM/disk. So... don't leave this running unattended? At least not without additional configuration. 

That's it! Hope it's helpful. 

<!--more-->

```python
import json
import flask
import uuid
import os

os.makedirs('requests', exist_ok=True)

app = flask.Flask(__name__)
methods = ["GET", "POST", "PATCH", "DELETE"]


@app.route("/", methods=methods, defaults={"path": ""})
@app.route("/<path:path>", methods=methods)
def hello_world(path):
    id = uuid.uuid1().hex

    data = {
        "uuid": id,
        "headers": dict(flask.request.headers),
        "path": path,
        "data": flask.request.data.decode(),
        "form": dict(flask.request.form),
        "json": flask.request.get_json(),
    }

    js = json.dumps(data, indent=2, default=str)
    with open(os.path.join('requests', f'{id}.json'), 'w') as f:
        f.write(js)

    print(f'=== {id} ===\n{js}\n')

    return flask.jsonify(data)


if __name__ == "__main__":
    app.run()
```