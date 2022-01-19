import json
import os
import logging
import requests
from bs4 import BeautifulSoup
from base64 import b64decode
import traceback
import cgi
import io
from urllib.parse import urlparse, unquote

def get_content_telegraaf(dom) -> str:
    src = dom.select('html.no-js head script[data-react-helmet="true"]')
    ld = json.loads(src[0].text)
    return (ld['headline'], ld['articleBody'])

sites = {
    "www.telegraaf.nl": get_content_telegraaf,
}

def get_content(url: str) -> str:
    page = requests.get(url).text
    dom = BeautifulSoup(page, features="html.parser")

    hostname = urlparse(url).hostname
    fn = sites[hostname]
    return fn(dom)

# Logging is cool!
logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

home_template = '''
<!doctype html>
<html>
<body>
    <form action="#" method="POST">
        <label for="url">Which page should we fix?</label>
        <br />
        <input name="url" id="url" type="url" placeholder="URL"></input>
        <br />
        <button type="submit">Fix</button>
    </form>
    <script>
        const url = `${location.pathname}/fix`;
        const form = document.getElementsByTagName('form')[0];
        form.action = url;
    </script>
</body>
</html>
'''

def get_form_data(event) -> dict:
    fp = io.BytesIO(event['body'].encode('utf-8'))
    pdict = cgi.parse_header(event['headers']['Content-Type'])[1]
    if 'boundary' in pdict:
        pdict['boundary'] = pdict['boundary'].encode('utf-8')
    pdict['CONTENT-LENGTH'] = len(event['body'])
    return cgi.parse_multipart(fp, pdict)

def home(_event, _context):
    try:
        return ok_html(home_template)
    except Exception:
        return error(traceback.format_exc())

def fix(event, context):
    try:
        formdata = b64decode(event['body'])
        quoted_url = formdata[4:] # LAZYYYYY
        url = unquote(quoted_url)
        headline, content = get_content(url)
        return ok_article(headline, content)
    except Exception:
        return error(traceback.format_exc())

    #if event['requestContext']['http']['method'] != 'POST' or \
            #not event['body']:
        #return ERROR_RESPONSE

def ok_json(src: str) -> dict:
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(src),
    }

def ok_html(src: str) -> dict:
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': src,
    }

def ok_article(title, content) -> dict:
    paragraphs = '\n'.join(f"<p>{line}</p>" for line in content.split('\n'))
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': f'<!doctype html><html><head><meta charset="utf-8"></head><title>helegaaf: {title}</title><body><h1>{title}</h1><p>{paragraphs}</p></body></html>',
    }

def error(error: str) -> dict:
    return {
        'statusCode': 400,
        'headers': {'Content-Type': 'text/html'},
        'body': f'<!doctype html><html><head><meta charset="utf-8"><title>helegaaf: error</title></head><body><h1>Oops, something went wrong!</h1><pre>{error}</pre></body></html>',
    }
