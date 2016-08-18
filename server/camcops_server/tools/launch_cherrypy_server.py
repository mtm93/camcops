#!/usr/bin/env python

import argparse
import logging
import os

import cherrypy

from ..camcops import application as wsgi_application
from ..cc_modules.cc_constants import STATIC_ROOT_DIR, URL_ROOT_STATIC

log = logging.getLogger(__name__)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = '/'  # TODO: from config file?


class Missing(object):
    """Basic web interface to say "not here"."""
    config = {
        '/': {
            # Anything so as to prevent complaints about an empty config.
            'tools.sessions.on': False,
        }
    }

    @cherrypy.expose
    def index(self):
        return "[CherryPy server says:] Nothing to see here. Wrong URL path."


def start_server(opts):
    """
    Start CherryPy server
    """

    # if opts.daemonize and opts.server_user and opts.server_group:
    #     # ensure the that the daemon runs as specified user
    #     change_uid_gid(opts.server_user, opts.server_group)

    cherrypy.config.update({
        'server.socket_host': opts.host,
        'server.socket_port': opts.port,
        'server.thread_pool': opts.threads,
        'server.thread_pool_max': opts.threads,
        'server.server_name': opts.server_name,
        'server.log_screen': opts.log_screen,
    })
    if opts.ssl_certificate and opts.ssl_private_key:
        cherrypy.config.update({
            'server.ssl_module': 'builtin',
            'server.ssl_certificate': opts.ssl_certificate,
            'server.ssl_private_key': opts.ssl_private_key,
        })

    log.info("Starting on host: {}".format(opts.host))
    log.info("Starting on port: {}".format(opts.port))
    log.info("Static files will be served from filesystem path: {}".format(
        STATIC_ROOT_DIR))
    log.info("Static files will be served at URL path: {}".format(
        URL_ROOT_STATIC))
    log.info("CRATE will be at: {}".format(opts.root_path))
    log.info("Thread pool size: {}".format(opts.threads))
    log.info("Thread pool max size: {}".format(opts.threads))

    static_config = {
        '/': {
            'tools.staticdir.root': STATIC_ROOT_DIR,
            'tools.staticdir.debug': opts.debug_static,
        },
        URL_ROOT_STATIC: {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': '',
        },
    }
    cherrypy.tree.mount(Missing(), '', config=static_config)
    cherrypy.tree.graft(wsgi_application, opts.root_path)

    try:
        cherrypy.engine.start()
        cherrypy.engine.block()
    except KeyboardInterrupt:
        cherrypy.engine.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--host', type=str, default="127.0.0.1",
        help="hostname to listen on (default: 127.0.0.1)")
    parser.add_argument(
        '--port', type=int, default=8088,
        help="port to listen on (default: 8088)")
    parser.add_argument(
        "--server_name", type=str, default="localhost",
        help="CherryPy's SERVER_NAME environ entry (default: localhost)")
    # parser.add_argument(
    #     "--daemonize", action="store_true",
    #     help="whether to detach from terminal (default: False)")
    # parser.add_argument(
    #     "--pidfile", type=str,
    #     help="write the spawned process ID to this file")
    # parser.add_argument(
    #     "--workdir", type=str,
    #     help="change to this directory when daemonizing")
    parser.add_argument(
        "--threads", type=int, default=1,
        help="Number of threads for server to use (default: 1)")
    # TODO: fix: CamCOPS is not thread-safe (and will abort with >1 thread)
    parser.add_argument(
        "--ssl_certificate", type=str,
        help="SSL certificate file "
             "(e.g. /etc/ssl/certs/ssl-cert-snakeoil.pem)")
    parser.add_argument(
        "--ssl_private_key", type=str,
        help="SSL private key file "
             "(e.g. /etc/ssl/private/ssl-cert-snakeoil.key)")
    # parser.add_argument(
    #     "--server_user", type=str, default="www-data",
    #     help="user to run daemonized process (default: www-data)")
    # parser.add_argument(
    #     "--server_group", type=str, default="www-data",
    #     help="group to run daemonized process (default: www-data)")

    parser.add_argument(
        "--log_screen", dest="log_screen", action="store_true",
        help="log access requests etc. to terminal (default)")
    parser.add_argument(
        "--no_log_screen", dest="log_screen", action="store_false",
        help="don't log access requests etc. to terminal")
    parser.set_defaults(log_screen=True)

    parser.add_argument(
        "--debug_static", action="store_true",
        help="show debug info for static file requests")
    parser.add_argument(
        "--root_path", type=str, default=DEFAULT_ROOT,
        help="Root path to serve CRATE at. Default: {}".format(
            DEFAULT_ROOT))
    # parser.add_argument(
    #     "--stop", action="store_true",
    #     help="stop server")
    opts = parser.parse_args()

    rootlogger = logging.getLogger()
    rootlogger.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)

    # Start the webserver
    log.info('starting server with options {}'.format(opts))
    start_server(opts)


if __name__ == '__main__':
    main()