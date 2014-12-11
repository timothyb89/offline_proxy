"""
An offline caching proxy..
"""

import sys
import json
import os
import time

from threading import Thread

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler


#: The minimum time to wait
DELAYED_WRITE_THRESHOLD = 5.0
DELAYED_WRITE_SLEEP = 1.0


class DelayedWriteHelper(Thread):
    """
    A background that that will automatically store proxy metadata after a
    short period of inactivity.
    """

    def __init__(self, proxy):
        super(DelayedWriteHelper, self).__init__()

        self.proxy = proxy

        self.running = False
        self.last_poke_time = time.time()

    def run(self):
        self.running = True

        while True:
            time.sleep(DELAYED_WRITE_SLEEP)

            current_time = time.time()
            if current_time - self.last_poke_time > DELAYED_WRITE_THRESHOLD:
                break

        # the cache (probably a usb disk) may have been removed
        # if so, the wrapper should have called OfflineProxy.unset_cache()
        if not self.proxy.cache_meta_path:
            print "Cache went away, unable to save metadata!"
            return

        # threshold exceeded, force a write
        self.proxy.write_cache(self.proxy.cache_meta_path)
        print "Cache metadata written to %s" % self.proxy.cache_meta_path

        self.running = False

    def poke(self):
        self.last_poke_time = time.time()


class OfflineProxy:

    def __init__(self):
        self.cache = None
        self.cache_path = None
        self.cache_meta_path = None

        self.write_delay_thread = None

    def init_cache(self, path):
        self.cache_meta_path = path
        self.cache_path = os.path.dirname(path)

        if not os.path.isfile(path):
            self.cache = {}
        else:
            with open(path, 'r') as f:
                self.cache = json.load(f)

    def write_cache(self, path):
        if self.cache is None:
            return

        with open(path, 'wb') as f:
            json.dump(self.cache, f, indent = 4, separators = (',', ': '))
            f.write('\n')

    def unset_cache(self):
        """
        Unsets the cache. The server will throw errors until the cache is reinitialized.
        """
        self.cache = None
        self.cache_path = None
        self.cache_meta_path = None

    def poke_write_thread(self):
        """
        Creates or updates the delayed write thread.
        """
        if self.write_delay_thread and self.write_delay_thread.running:
            self.write_delay_thread.poke()
        else:
            self.write_delay_thread = DelayedWriteHelper(self)
            self.write_delay_thread.start()

    def get_path(self, cache_entry):
        return os.path.join(self.cache_path, cache_entry['path'])


def create_server(proxy, address = ('', 8080)):
    # crappy scope workaround to avoid cluttering globals

    class ProxyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            cache = proxy.cache
            if cache is None:
                print "No cache mounted!"
                self.send_error(404,'Not found: %s' % self.path)
                return


            if self.path in cache and cache[self.path]['local']:
                # serve from cache
                entry = cache[self.path]

                self.send_response(entry['status'])

                for key, value in entry['headers'].iteritems():
                    self.send_header(key, value)

                fpath = proxy.get_path(entry)
                self.send_header('Content-Length', os.stat(fpath).st_size)

                self.end_headers()

                with open(fpath, 'r') as f:
                    self.wfile.write(f.read())

                return
            else:
                # record in cache to fetch later
                cache[self.path] = {
                    'local': False
                }

                proxy.poke_write_thread()

                self.send_error(404,'Not found: %s' % self.path)
                return

    return HTTPServer(address, ProxyHandler)


def main():
    proxy = OfflineProxy()

    try:
        server = create_server(proxy)
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    print "done"


if __name__ == '__main__':
    main()
