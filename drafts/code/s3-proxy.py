import boto3
import mimetypes
import flask

app = flask.Flask(__name__)

BUCKET = 'ed.edim.co'

@app.route('/<path:path>')
def file(path):
    s3 = boto3.resource('s3')
    obj = s3.Object(BUCKET, path).get()
    content = obj['Body'].read()

    # content = boto3.resource('s3').Object(BUCKET, path).get()['Body'].read()

    mimetype, encoding = mimetypes.guess_type(path)

    return flask.Response(
        content,
        mimetype = mimetype
    )

if __name__ == "__main__":
    app.run(host = '0.0.0.0', debug = True)