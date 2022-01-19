# helegraaf

Fix readability issues on the website of certain low-quality news publications :wink:

## Usage

### Reqiurements

- An AWS key configured locally, see [here](https://serverless.com/framework/docs/providers/aws/guide/credentials/).
- Python 3.9. (try pyenv)
- NodeJS. I tested with v17.3.0

### Installing

```
# Install the Serverless Framework using either your distro's package manager...
$ sudo pacman -S serverless

# ...or npm
$ npm install serverless -g

# Install the necessary node_modules into this directory
$ npm install

# Generate a reasonably long (32 chars is ok) random string
$ printf '%s: "%s"\n' PATH_TOKEN "$(tr -dc A-Za-z0-9 < /dev/urandom | head -c 32)" >> serverless.env.yml

# Deploy it!
$ serverless deploy
```

Now, go to the url from the deployment output that doesn't end in `/fix` and paste in an article from your "favorite" newspaper. Handy!
