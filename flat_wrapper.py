import os

from offline_proxy import OfflineProxy, create_server


def main():
    proxy = OfflineProxy()
    proxy.init_cache(os.path.join(os.getcwd(), 'metadata.json'))
    proxy.write_cache(proxy.cache_meta_path)

    server = create_server(proxy)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()