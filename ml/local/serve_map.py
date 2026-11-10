"""Open data/local/route_groups.html through a local web server, so the OpenStreetMap tiles load
(the tile server refuses pages opened as file://, which send no Referer).

    python ml/local/serve_map.py [--port 8765]

Listens on 127.0.0.1 only: the folder holds the survey positions and frames, which must not be
reachable from other computers. Stop it with Ctrl+C.
"""

import argparse
import functools
import http.server
import threading
import webbrowser

from common import OUT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--page', default='route_groups.html')
    ap.add_argument('--no-browser', action='store_true')
    a = ap.parse_args()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', a.port), handler)
    url = f'http://127.0.0.1:{a.port}/{a.page}'
    print(f'Serving {OUT} at {url} (Ctrl+C to stop)', flush=True)
    if not a.no_browser:
        threading.Timer(0.5, webbrowser.open, [url]).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
