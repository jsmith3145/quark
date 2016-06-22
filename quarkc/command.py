# Copyright 2015 datawire. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Quark compiler.

Usage:
  quark [options] install [ (--java | --python | --javascript | --ruby)... | --all ] [<file>]...
  quark [options] compile [ -o DIR ] [ (--java | --python | --javascript | --ruby)... | --all ] <file>...
  quark [options] run ( --java | --python | --javascript | --ruby ) <file> [ -- <args>... ]
  quark [options] docs [<file>]...
  quark -h | --help | help
  quark --version

Commands:
  compile               Compile and emit code in the target language(s).
  install               Compile, build, and install code in the target language(s).
                        If no file is given only the Quark standard library package is
                        installed.
  run                   Run the main() function from the package namespace; the quark
                        file must already be installed.
  docs                  Output API documentation in HTML.

Options:
  -h --help             Show this screen.
  --version             Show version.
  -v --verbose          Show more detail.

  -o DIR, --output DIR  Target directory for output files. [default: output]

  --all                 Install/emit code for all available target languages.
                        [this is the default if no targets are specified]

  --java                Install/emit Java code.
  --ruby                Install/emit Ruby code.
  --python              Install/emit Python code.
  --javascript          Install/emit JavaScript code.

  --version-warning     Treat compiler-version-related errors as warnings.
"""

import sys
import logging
import datetime
import textwrap

from docopt import docopt

import _metadata
import compiler
import backend
import helpers
import shell
from .exceptions import QuarkError


class ProgressHandler(logging.Handler):

    def __init__(self, *args, **kwargs):
        self.verbose = kwargs.pop("verbose", False)
        logging.Handler.__init__(self, *args, **kwargs)
        self.stream = sys.stdout
        self.last = logging.NOTSET
        self.do_debug = False

        def spinner():
            while True:
                yield "."
                yield ""
                yield ""
                yield ""
        self.spinner = spinner()

    def emit(self, record):
        msg = self.format(record)
        if record.levelno < logging.INFO:
            if self.last < logging.INFO:
                if self.last == logging.NOTSET:
                    prefix = ""
                    dbg = " (0->d) "
                else:
                    prefix = "\n"
                    dbg = " (d->d) "
                postfix = ""
            else:
                prefix = "\n"
                dbg = " (i->d) "
                postfix = ""
            if not self.verbose:
                prefix = ""
                postfix = ""
                msg = next(self.spinner)
                dbg = ""
        elif record.levelno == logging.INFO:
            if self.last < logging.INFO:
                if self.last == logging.NOTSET:
                    prefix = ""
                    dbg = " (0->i) "
                else:
                    prefix = "\n"
                    dbg = " (d->i) "
                postfix = " ..."
            else:
                prefix = " done.\n"
                dbg = " (i->i) "
                postfix = " ..."
        elif record.levelno == logging.WARNING:
            if self.last < logging.INFO:
                prefix = "\n"
                dbg = " (d->w) "
                postfix = "\n"
            else:
                prefix = " done.\n"
                dbg = " (i->w) "
                postfix = "\n"
        else:
            if self.last < logging.INFO:
                prefix = "\n"
                dbg = " (d->e) "
                postfix = "\n"
            else:
                prefix = "\n"
                dbg = " (i->e) "
                postfix = "\n"
        self.last = record.levelno
        if self.do_debug:
            prefix += dbg
        self.stream.write("%s%s%s" % (prefix, msg, postfix))
        self.stream.flush()


def main(args):
    if args["help"]:
        print __doc__.rstrip()
        return None

    do_log = not args["run"] or args["--verbose"]
    if do_log:
        if args["--verbose"]:
            shell.COMMAND_DEFAULTS["mvn"] = "mvn"
        logging.basicConfig(level=logging.DEBUG)
        log = logging.getLogger("quark")
        log.propagate = False
        hnd = ProgressHandler(verbose=args["--verbose"])
        log.addHandler(hnd)
        hnd.setFormatter(logging.Formatter("%(message)s"))

    helpers.Code.identifier = "Quark %s run at %s" % (_metadata.__version__, datetime.datetime.now())

    java = args["--java"]
    ruby = args["--ruby"]
    python = args["--python"]
    javascript = args["--javascript"]

    all = args["--all"] or not (java or python or javascript or ruby)

    output = args["--output"]

    try:
        shell.command_log.info("Checking environment")
        backends = []
        if java or all:
            if args["install"]: shell.check("mvn")
            backends.append(backend.Java)
        if ruby or all:
            if args["install"]: shell.check("gem")
            backends.append(backend.Ruby)
        if python or all:
            if args["install"]:
                shell.check("python")
                shell.check("pip")
            backends.append(backend.Python)
        if javascript or all:
            if args["install"]: shell.check("npm")
            backends.append(backend.JavaScript)

        filenames = args["<file>"] or [compiler.join(None, compiler.BUILTIN_FILE)]
        for url in filenames:
            c = compiler.Compiler()
            c.version_warning = args["--version-warning"]
            if args["install"]:
                compiler.install(c, url, *backends)
            elif args["compile"]:
                compiler.compile(c, url, output, *backends)
            elif args["run"]:
                compiler.run(c, url, args["<args>"], *backends)
            elif args["docs"]:
                compiler.make_docs(c, url, output)
            else:
                assert False
    except (KeyboardInterrupt, QuarkError) as err:
        if not args["run"]:
            shell.command_log.error("")
        return err
    except:  # pylint: disable=bare-except
        if do_log:
            import inspect
            ast_stack = helpers.format_ast_stack(inspect.trace())
            shell.command_log.error("\n -- snip --\nInternal compiler error", exc_info=True)
            shell.command_log.error("\nCompiler was looking at:\n%s\n" % ast_stack)
        instructions = textwrap.dedent("""\

        Your code triggered an internal compiler error.

        Please report the issue at https://github.com/datawire/quark/issues
        """)
        if do_log:
            instructions += textwrap.dedent("""\

            Please attach the above report up until the -- snip -- line with the issue.
            If at all possible also attach the quark file that caused the error.
            """)
        else:
            instructions += textwrap.dedent("""\

            Please re-run the quark command with --verbose flag to get the full report.
            """)
        return instructions

    shell.command_log.warn("Done")


def call_main():
    exit(main(docopt(__doc__, version="Quark %s" % _metadata.__version__)))


if __name__ == "__main__":
    call_main()
