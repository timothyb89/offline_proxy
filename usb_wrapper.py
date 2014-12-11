"""
A wrapper for `offline_proxy` that uses removable media for its datastore. Uses
pyudev to monitor for device insertion, and updates the proxy with the

"""
import os

from offline_proxy import OfflineProxy, create_server

from threading import Thread
from time import sleep

from twisted.internet import reactor
from twisted.web.server import Site

from pyudev import Context, Monitor, MonitorObserver


CACHE_DIRECTORY = 'cache'
CACHE_METADATA = 'metadata.json'


_proxy = None
_monitor_thread = None

_current_device = None
_current_mountpoint = None

def handle_mount(device, mount):
    global _proxy, _current_device, _current_mountpoint

    print "Device %s mounted, initializing cache..." % device.get("DEVNAME")

    _current_device = device
    _current_mountpoint = mount['path']

    dir = os.path.join(_current_mountpoint, CACHE_DIRECTORY)
    if not os.path.exists(dir):
        os.mkdir(dir)

    _proxy.init_cache(os.path.join(dir, CACHE_METADATA))

    # write initial (probably empty) cache immediately
    _proxy.write_cache(_proxy.cache_meta_path)


def get_mounts():
    mounts = {}

    with open('/proc/mounts', 'r') as f:
        for line in f:
            params = line.split()

            device = params[0]
            mounts[device] = {
                'path': params[1],
                'type': params[2],
                'options': params[3].split(',')
            }

    return mounts


def wait_for_mount(device):
    paths = [ c.get('DEVNAME') for c in device.children ]

    print "Waiting for mount of any device: %r" % paths

    # try for a while to let the OS / user mount the disk.
    # depending on DE this may require the user to mount the drive, so we'll
    # give it a fairly generous amount of time.
    for i in range(10):
        sleep(1.0)

        # attempt to pair one of the partition devices to a mountpoint
        mounts = get_mounts()
        for path in paths:
            if path in mounts:
                mount = mounts[path]

                # skip if we can't write to the drive (permissions notwithstanding)
                if not 'rw' in mount['options']:
                    continue

                handle_mount(device, mounts[path])
                return

    print "No valid mountpoint could be found for device %s for partitions: %r"\
          % (device.get("DEVNAME"), paths)


def device_event(action, device):
    global _current_device, _current_mountpoint, _proxy

    print "event: ", action, "device:", device

    # only look for USB devices
    if device.get('ID_BUS') != 'usb':
        return

    # if a new device is inserted and we don't already have one, wait for one
    # of its partitions to be mounted
    if action == 'add' and _current_device is None:
        print "Device %s inserted, waiting for mount..." % device.get("DEVNAME")

        t = Thread(target = wait_for_mount, args = [device])
        t.start()
    elif action == 'remove' and _current_device == device:
        _current_device = None
        _current_mountpoint = None
        _proxy.unset_cache()

        print "Device %s removed, cache unset." % device.get("DEVNAME")

    # ignore change events


def monitor_background():
    c = Context()

    monitor = Monitor.from_netlink(c)
    monitor.filter_by("block", "disk")

    obs = MonitorObserver(monitor, device_event)
    obs.start()


def main():
    global _proxy, _monitor_thread

    _proxy = OfflineProxy()

    _monitor_thread = Thread(target = monitor_background)
    _monitor_thread.start()

    server = create_server(_proxy)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
