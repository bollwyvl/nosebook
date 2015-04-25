import logging
import os
import re
import json
from copy import copy

try:
    # py3
    from queue import Empty

    def isstr(s):
        return isinstance(s, str)
except ImportError:
    # py2
    from Queue import Empty

    def isstr(s):
        return isinstance(s, basestring)  # noqa

from unittest import TestCase

from nose.plugins import Plugin

from IPython.kernel.tests import utils


try:
    from IPython.nbformat.converter import convert
    from IPython.nbformat.reader import reads
    IPYTHON_VERSION = 3
except ImportError:
    from IPython.nbformat.convert import convert
    from IPython.nbformat.reader import reads
    IPYTHON_VERSION = 2

NBFORMAT_VERSION = 4

__version__ = "0.4.0"

log = logging.getLogger("nose.plugins.nosebook")


class NosebookTwo(object):
    """
    Implement necessary functions against the IPython 2.x API
    """

    def newKernel(self, nb):
        """
        generate a new kernel
        """
        manager, kernel = utils.start_new_kernel()
        return kernel


class NosebookThree(object):
    """
    Implement necessary functions against the IPython 3.x API
    """
    def newKernel(self, nb):
        """
        generate a new kernel
        """
        manager, kernel = utils.start_new_kernel(
            kernel_name=nb.metadata.kernelspec.name
        )
        return kernel

NosebookVersion = NosebookThree

if IPYTHON_VERSION == 2:
    NosebookVersion = NosebookTwo


def dump_canonical(obj):
    return json.dumps(obj, indent=2, sort_keys=True)


class Nosebook(NosebookVersion, Plugin):
    """
    A nose plugin for discovering and executing IPython notebook cells
    as tests
    """
    name = "nosebook"

    def options(self, parser, env=os.environ):
        """
        advertise options
        """

        self.testMatchPat = env.get('NOSEBOOK_TESTMATCH',
                                    r'.*[Tt]est.*\.ipynb$')

        self.testMatchCellPat = env.get('NOSEBOOK_CELLMATCH',
                                        r'.*')

        parser.add_option(
            "--nosebook-match",
            action="store",
            dest="nosebookTestMatch",
            metavar="REGEX",
            help="Notebook files that match this regular expression are "
                 "considered tests.  "
                 "Default: %s [NOSEBOOK_TESTMATCH]" % self.testMatchPat,
            default=self.testMatchPat
        )

        parser.add_option(
            "--nosebook-match-cell",
            action="store",
            dest="nosebookTestMatchCell",
            metavar="REGEX",
            help="Notebook cells that match this regular expression are "
                 "considered tests.  "
                 "Default: %s [NOSEBOOK_CELLMATCH]" % self.testMatchCellPat,
            default=self.testMatchCellPat
        )

        parser.add_option(
            "--nosebook-scrub",
            action="store",
            default=env.get('NOSEBOOK_SCRUB'),
            dest="nosebookScrub",
            help="a quoted regex, or JSON obj/list of regexen to "
                 "scrub from cell outputs "
                 "[NOSEBOOK_SCRUB]")

        super(Nosebook, self).options(parser, env=env)

    def configure(self, options, conf):
        """
        apply configured options
        """
        super(Nosebook, self).configure(options, conf)

        self.testMatch = re.compile(options.nosebookTestMatch).match
        self.testMatchCell = re.compile(options.nosebookTestMatchCell).match

        scrubs = []
        if options.nosebookScrub:
            try:
                scrubs = json.loads(options.nosebookScrub)
            except Exception:
                scrubs = [options.nosebookScrub]

        if isstr(scrubs):
            scrubs = {
                scrubs: "<...>"
            }
        elif not isinstance(scrubs, dict):
            scrubs = dict([
                (scrub, "<...%s>" % i)
                for i, scrub in enumerate(scrubs)
            ])

        self.scrubMatch = {
            re.compile(scrub): sub
            for scrub, sub in scrubs.items()
        }

    def wantModule(self, *args, **kwargs):
        """
        we don't handle actual code modules!
        """
        return False

    def _readnb(self, filename):
        with open(filename) as f:
            return reads(f.read())

    def readnb(self, filename):
        try:
            nb = self._readnb(filename)
        except Exception as err:
            log.info("could not be parse as a notebook %s\n%s",
                     filename,
                     err)
            return False

        return convert(nb, NBFORMAT_VERSION)

    def codeCells(self, nb):
        for cell in nb.cells:
            if cell.cell_type == "code":
                yield cell

    def wantFile(self, filename):
        """
        filter files to those that match nosebook-match
        """

        log.info("considering %s", filename)

        if self.testMatch(filename) is None:
            return False

        nb = self.readnb(filename)

        for cell in self.codeCells(nb):
            return True

        log.info("no `code` cells in %s", filename)

        return False

    def loadTestsFromFile(self, filename):
        """
        find all tests in a notebook.
        """
        nb = self.readnb(filename)

        kernel = self.newKernel(nb)

        for cell_idx, cell in enumerate(self.codeCells(nb)):
            if self.testMatchCell(cell.source) is not None:
                yield NoseCellTestCase(
                    cell,
                    cell_idx,
                    kernel,
                    filename=filename,
                    scrubs=self.scrubMatch
                )


class NoseCellTestCase(TestCase):
    """
    A test case for a single cell.
    """
    IGNORE_TYPES = ["execute_request", "execute_input", "status", "pyin"]
    STRIP_KEYS = ["execution_count", "traceback", "prompt_number", "source"]

    def __init__(self, cell, cell_idx, kernel, *args, **kwargs):
        """
        initialize this cell as a test
        """

        self.cell = self.sanitizeCell(cell)
        self.cell_idx = cell_idx
        self.scrubs = kwargs.pop("scrubs", [])
        self.filename = kwargs.pop("filename", "")

        self.kernel = kernel
        self.iopub = self.kernel.iopub_channel

        self.runTest.__func__.__doc__ = self.id()

        super(NoseCellTestCase, self).__init__(*args, **kwargs)

    def id(self):
        return "%s#%s" % (self.filename, self.cell_idx)

    def cellCode(self):
        if hasattr(self.cell, "source"):
            return self.cell.source
        return self.cell.input

    def runTest(self):
        self.kernel.execute(self.cellCode())

        outputs = []
        msg = None

        while self.shouldContinue(msg):
            try:
                msg = self.iopub.get_msg(block=True, timeout=1)
            except Empty:
                continue

            if msg["msg_type"] not in self.IGNORE_TYPES:
                output = self.transformMessage(
                    msg,
                    self.cell.outputs[len(outputs)]
                )
                outputs.append(output)

        scrub = lambda x: dump_canonical(list(self.scrubOutputs(x)))

        scrubbed = scrub(outputs)
        expected = scrub(self.cell.outputs)

        self.assertEqual(scrubbed, expected, "\n{}\n\n{}".format(
            scrubbed,
            expected
        ))

    def scrubOutputs(self, outputs):
        """
        remove all scrubs from output data and text
        """
        for output in outputs:
            out = copy(output)

            for scrub, sub in self.scrubs.items():
                def _scrubLines(lines):
                    if isstr(lines):
                        return re.sub(scrub, sub, lines)
                    else:
                        return [re.sub(scrub, sub, line) for line in lines]

                if "text" in out:
                    out["text"] = _scrubLines(out["text"])

                if "data" in out:
                    if isinstance(out["data"], dict):
                        for mime, data in out["data"].items():
                            out["data"][mime] = _scrubLines(data)
                    else:
                        out["data"] = _scrubLines(out["data"])
            yield out

    def stripKeys(self, d):
        """
        remove keys from STRIP_KEYS to ensure comparability
        """
        for key in self.STRIP_KEYS:
            d.pop(key, None)
        return d

    def sanitizeCell(self, cell):
        """
        remove non-reproducible things
        """
        for output in cell.outputs:
            self.stripKeys(output)
        return cell

    def transformMessage(self, msg, expected):
        """
        transform a message into something like the notebook
        """
        SWAP_KEYS = {
            "output_type": {
                "pyout": "execute_result",
                "pyerr": "error"
            }
        }

        output = {
            u"output_type": msg["msg_type"]
        }
        output.update(msg["content"])

        output = self.stripKeys(output)
        for key, swaps in SWAP_KEYS.items():
            if key in output and output[key] in swaps:
                output[key] = swaps[output[key]]

        if "data" in output and "data" not in expected:
            output["text"] = output["data"]
            del output["data"]

        return output

    def shouldContinue(self, msg):
        """
        determine whether the current message is the last for this cell
        """
        if msg is None:
            return True

        return not (msg["msg_type"] == "status" and
                    msg["content"]["execution_state"] == "idle")
