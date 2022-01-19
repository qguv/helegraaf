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

# set up cloudwatch logs~
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

article_template = '''
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>helegaaf: {title}</title>

    <style>
        html {{
            background-color: #222;
            padding: 5px;
        }}

        body {{
            padding: 1em 2em;
            margin: auto;
            color: white;
            max-width: 800px;
            font-family: sans-serif;
        }}

        h1 {{
            margin-bottom: 40px;
            text-align: center;
        }}

        h2 {{
            margin-top: 40px;
            text-align: left;
        }}

        h1, h2 {{
            font-family: serif;
        }}

        p:first-of-type::first-letter {{
            font-size: 300%;
            font-weight: bold;
            font-family: serif;
        }}

        p {{
            text-align: justify;
            line-height: 1.5em;
        }}
    </style>

</head>
<body>
    <h1>{title}</h1>
    {paragraphs}
</body>
</html>
'''


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


def wrap_tag(s) -> str or None:
    has_punctuation = any((c in '.?!') for c in s)
    tag = 'p' if has_punctuation else 'h2'
    return f"<{tag}>{s}</{tag}>"


def fmt_article(content):
    for line in content.split('\n'):
        line = line.strip()
        if line:
            tag = wrap_tag(line)
            if tag:
                yield tag


def ok_article(title, content) -> dict:
    paragraphs = '\n'.join(fmt_article(content))
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/html'},
        'body': article_template.format(title=title, paragraphs=paragraphs),
    }


def error(error: str) -> dict:
    return {
        'statusCode': 400,
        'headers': {'Content-Type': 'text/html'},
        'body': f'<!doctype html><html><head><meta charset="utf-8"><title>helegaaf: error</title></head><body><h1>Oops, something went wrong!</h1><pre>{error}</pre></body></html>',
    }
