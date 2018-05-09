# Glasnost

Glasnost is a proxy service to authenticate requests for static assets stored in AWS S3 with Google OAuth.

## Installation

```
# Clone this repo
git clone git@github.com:spbrien/glasnost.git

# Install with pip
cd glasnost
pip install -r requirements

# Configure your application
cp app/settings.template.py app/settings.py

# Edit app/settings.py with your configuration
# Then run a local dev server
./run.sh
```

Visiting [http://localhost:5000](http://localhost:5000) will fetch and return an `index.html` file if it is present in your S3 bucket, otherwise a `404` error. Any path sent to Glosnost will return the S3 object having a key that matches the provided path. So `http://localhost:5000/foo/bar` will return the S3 object `foo/bar`, otherwise a `404` error.
