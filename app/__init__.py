from urllib2 import Request, urlopen, URLError

from flask import (
    Flask,
    Blueprint,
    session,
    request,
    redirect,
    url_for,
    make_response
)
from flask_oauth import OAuth

import requests

import settings
import bucketstore

# TODO: Implement remote session storage for stateless operation
# TODO: Instead of plain http proxy, proxy to S3 Bucket files

# --------------------------------------
# Create Flask Application
# --------------------------------------

app = Flask(__name__)
app.config.from_object(settings)

# --------------------------------------
# Setup Google OAuth
# --------------------------------------

oauth = Blueprint('oauth', __name__)
authentication = OAuth()
google = authentication.remote_app(
    'google',
    base_url='https://www.google.com/accounts/',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    request_token_url=None,
    request_token_params={
        'scope': 'https://www.googleapis.com/auth/userinfo.email',
        'response_type': 'code'
    },
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_method='POST',
    access_token_params={
        'grant_type': 'authorization_code'
    },
    consumer_key=app.config.get('GOOGLE_CLIENT_ID', None),
    consumer_secret=app.config.get('GOOGLE_CLIENT_SECRET', None)
)

REDIRECT_URI = '/authorized'

# --------------------------------------
# Setup S3 Access
# --------------------------------------

bucketstore.login(
    app.config.get('AWS_ACCESS_KEY_ID'),
    app.config.get('AWS_SECRET_ACCESS_KEY')
)
bucket = bucketstore.get(app.config.get('AWS_BUCKET'), create=False)

# --------------------------------------
# Main Proxy Route
# --------------------------------------

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    if not path or path == '':
        path = 'index.html'

    # Process Auth
    access_token = session.get('token')
    if access_token is None:
        return redirect(url_for('login'))

    headers = {'Authorization': 'OAuth '+access_token}
    res = requests.get('https://www.googleapis.com/oauth2/v1/userinfo', headers=headers)
    if res.status_code != 200:
        return redirect(url_for('login'))

    res_body = res.json()
    if res_body.get('hd', None) != app.config.get('GOOGLE_ORGANIZATION', None):
        return redirect(url_for('login'))

    # handle request
    if path in bucket.list():
        content = bucket.key(path)
        return make_response(content.get(), 200, {'Content-Type': content.content_type})

    return 'Not Found', 404


@app.route('/oauth/login/')
def login():
    callback=url_for('authorized', _external=True)
    return google.authorize(callback=callback)


# --------------------------------------
# Authorized Route
# --------------------------------------

@app.route('/oauth%s' % REDIRECT_URI)
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    # Create a new Server Issued token with the google access token
    session['token'] = access_token

    return redirect(url_for('index'))


# --------------------------------------
# Token Handling
# --------------------------------------

@google.tokengetter
def get_access_token():
    token = session.get('token', None)
    return token
