offline_proxy
=============

An offline caching proxy that takes advantage of error handling behaviors in
many applications to allow them to be used transparently without an active
internet connection.

In particular, this tool is intended to simplify offline package management by
allowing you to use your operating system's existing package management tools
(such as `apt-get`, `zypper`, ...) rather than difficult-to-use or buggy
dedicated offline package management tools.

Currently, it is designed to use a USB flash drive to move data between a
disconnected machine and another without a connection.

Application Requirements
------------------------

To use an application offline with this tool, it needs to support HTTP proxies
(preferably with the `http_proxy` environment variable). In the future this may
be extended to allow use of a hosts file modification to add support for
applications that don't 

Additionally, applications that need to download many files at once (such as
package managers) should handle server errors (in particular, 404 errors) by
simply ignoring them. This behavior allows the proxy to collect all of the
necessary URLs to download from a network-connected computer. Applications that
exit after the first error will still work, but they may prove to be somewhat
frustrating to use. For many tools (such as `apt-get`), "ignore all" is the
default mode and will work without issues, while other tools (such as `zypper`)
will prompt the user to ignore errors.

Dependencies
------------

`offline_proxy.py`:
    * base python 2.7 install

`usb_wrapper.py`:
    * pyudev

`client.py `:
    * requests

Usage with `usb_wrapper`
------------------------

The USB wrapper allows you to run the proxy using a USB storage device as a
datastore. It provides basic system integration to automatically mount and
unmount the datastore as you insert and remove the USB device.

To use, simply run `offline_proxy.py`. It will immediately begin waiting for a
valid device to be inserted. Insert a USB device, and (if necessary) mount it.
Many desktop environments (like Ubuntu) will automatically mount USB storage
devices. You should see an `initializing cache...` message once a valid storage
location is located.

Then, configure your application to use the proxy `http://localhost:8080/`. For
`apt-get`, you can do the following:

```bash
sudo bash # user environment variables don't apply on Ubuntu
export http_proxy="http://localhost:8080/"
sudo apt-get update
```

Any attempt to access the proxy should generate 404 errors - this is desired!
The URLs will be stored by the server and written to the USB device to be
downloaded later.

Run any commands needed to collect as many URLs as desired. Once finished, wait
a few seconds for the proxy to output a `Cache metadata written ...` message,
and then remove the USB device.

On a networked machine, insert the USB device. You should notice a new `cache`
folder. Put `client.py` inside it, and then run it from that directory:

```bash
cd /media/usb/cache/
python client.py
```

The URLs will be downloaded and stored to various `cache-` files in that
directory. When finished, you can remove the USB device and bring it back to
the disconnected machine.

If the `offline_proxy.py` is no longer running, start it again, and reinsert
the USB device. It should automatically locate the cache once the filesystem
has been mounted. Now, when you run the commands as before, like
`apt-get update`, the proxy will instead return the cached data.
