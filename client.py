"""

"""
import os
import json
import requests
import traceback

from random import sample
from string import digits, ascii_uppercase, ascii_lowercase


PATH = os.path.dirname(os.path.realpath(__file__))
METADATA_PATH = os.path.join(PATH, 'metadata.json')


def rand_fname(length = 16):
    # http://stackoverflow.com/a/15746092/549639
    chars = ascii_lowercase + ascii_uppercase + digits

    fname = 'cache-' + ''.join(sample(chars, length))

    if os.path.exists(os.path.join(PATH, fname)):
        return rand_fname(length)

    return fname


def download_entry(url, entry):
    response = requests.get(url)

    print "downloading %s: %d" % (url, response.status_code)

    entry['local'] = True
    entry['status'] = response.status_code

    # TODO: support more headers
    entry['headers'] = {}
    if 'content-type' in response.headers:
        entry['headers']['content-type'] = response.headers['content-type']

    fname = rand_fname()

    with open(os.path.join(PATH, fname), 'wb') as f:
        for chunk in response.iter_content():
            f.write(chunk)

    entry['path'] = fname

    print "Downloaded: %s (%d, %s)" % (
        url,
        response.status_code,
        response.headers['content-type'] if 'content-type' in response.headers else 'text/plain?'
    )


def main():
    # load original cache
    with open(METADATA_PATH, 'r') as f:
        cache = json.load(f)

    for url, entry in cache.iteritems():
        if not entry['local']:
            try:
                download_entry(url, entry)
            except:
                print "Skipping URL due to error:", url
                traceback.print_exc()
        #if entry['local'] is False and 'headers' in entry:
        #    entry['local'] = True

    # write updated cache
    with open(METADATA_PATH, 'wb') as f:
        json.dump(cache, f)

if __name__ == '__main__':
    main()