# -*- coding: utf-8 -*-
# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""conda is a tool for managing environments and packages.

conda provides the following commands:

    Information
    ===========

    info       : display information about the current install
    list       : list packages linked into a specified environment
    search     : print information about a specified package
    help       : display a list of available conda commands and their help
                 strings

    Package Management
    ==================

    create     : create a new conda environment from a list of specified
                 packages
    install    : install new packages into an existing conda environment
    update     : update packages in a specified conda environment


    Packaging
    =========

    package    : create a conda package in an environment

Additional help for each command can be accessed by using:

    conda <command> -h
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import sys

PARSER = None


def generate_parser():
    # Generally using `global` is an anti-pattern.  But it's the lightest-weight way to memoize
    # or do a singleton.  I'd normally use the `@memoize` decorator here, but I don't want
    # to copy in the code or take the import hit.
    global PARSER
    if PARSER is not None:
        return PARSER
    from .conda_argparse import generate_parser
    PARSER = generate_parser()
    return PARSER


def init_loggers(context=None):
    from logging import CRITICAL, getLogger
    from ..gateways.logging import initialize_logging, set_verbosity
    initialize_logging()
    if context and context.json:
        # Silence logging info to avoid interfering with JSON output
        for logger in ('conda.stdout.verbose', 'conda.stdoutlog', 'conda.stderrlog'):
            getLogger(logger).setLevel(CRITICAL + 1)

    if context and context.verbosity:
        set_verbosity(context.verbosity)


def _main(*args, **kwargs):
    if len(args) == 1:
        args = args + ('-h',)

    p = generate_parser()
    args = p.parse_args(args[1:])

    from ..base.context import context
    context.__init__(argparse_args=args)
    init_loggers(context)

    # used with main_pip.py
    post_parse_hook = kwargs.pop('post_parse_hook', None)
    if post_parse_hook:
        post_parse_hook(args, p)

    from .conda_argparse import do_call
    exit_code = do_call(args, p)
    if isinstance(exit_code, int):
        return exit_code


def main(*args, **kwargs):
    # conda.common.compat contains only stdlib imports
    from ..common.compat import ensure_text_type, init_std_stream_encoding

    init_std_stream_encoding()

    if not args:
        args = sys.argv

    args = tuple(ensure_text_type(s) for s in args)

    if len(args) > 1:
        try:
            argv1 = args[1].strip()
            if argv1.startswith('shell.'):
                from ..activate import main as activator_main
                return activator_main()
            elif argv1.startswith('..'):
                import conda.cli.activate as activate
                activate.main()
                return
        except Exception:
            _, exc_val, exc_tb = sys.exc_info()
            init_loggers()
            from ..exceptions import ExceptionHandler
            return ExceptionHandler().handle_exception(exc_val, exc_tb)

    from ..exceptions import conda_exception_handler
    # on Windows, we need to add to PATH so that we find the libraries
    #   associated with this specific env Without this, we see lots of openssl
    #   HTTPErrors because either incorrect libraries or no libraries are
    #   present
    if sys.platform == "win32":
        from ..activate import _Activator
        from ..base.context import context
        import os
        os.environ["PATH"] = _Activator._get_path_dirs(context.root_prefix) + os.environ["PATH"]
    return conda_exception_handler(_main, *args, **kwargs)


if __name__ == '__main__':
    sys.exit(main())
