import logging
import os
import re
import json
from copy import copy

try:
    from queue import Empty
except ImportError:
    from Queue import Empty

from unittest import TestCase

from nose.plugins import Plugin

from IPython.kernel.tests import utils

try:
    from IPython.nbformat import read
    NBFORMAT_VERSION = 4
    IPYTHON_VERSION = 3
except ImportError:
    from IPython.nbformat.reader import read
    NBFORMAT_VERSION = 3
    IPYTHON_VERSION = 2

__version__ = "0.3.0"


log = logging.getLogger("nose.plugins.nosebook")


class NosebookTwo(object):
    """
    Implement necessary functions against the IPython 2.x API
    """
    def _readnb(self, filename):
        with open(filename) as f:
            return read(f)

    def _cells(self, nb):
        for worksheet in nb.worksheets:
            for cell in worksheet.cells:
                yield cell


class NosebookThree(object):
    """
    Implement necessary functions against the IPython 3.x API
    """
    def _readnb(self, filename):
        return read(filename, NBFORMAT_VERSION)

    def _cells(self, nb):
        for cell in nb.cells:
            yield cell


class NoseCellTestCaseTwo(object):
    def cellCode(self):
        return self.cell.input


class NoseCellTestCaseThree(object):
    def cellCode(self):
        return self.cell.source


NosebookVersion = NosebookThree
NoseCellTestCaseVersion = NoseCellTestCaseThree

if IPYTHON_VERSION == 2:
    NosebookVersion = NosebookTwo
    NoseCellTestCaseVersion = NoseCellTestCaseTwo


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

        if isinstance(scrubs, str):
            scrubs = {scrubs: "<...>"}
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

    def readnb(self, filename):
        try:
            nb = self._readnb(filename)
        except Exception as err:
            log.info("could not be parse as a notebook %s\n%s",
                     filename,
                     err)
            return False
        return nb

    def codeCells(self, nb):
        for cell in self._cells(nb):
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

    def newKernel(self, nb):
        """
        generate a new kernel
        """
        manager, kernel = utils.start_new_kernel(
            kernel_name=nb.metadata.kernelspec.name
        )
        return kernel


class NoseCellTestCase(NoseCellTestCaseVersion, TestCase):
    """
    A test case for a single cell.
    """
    IGNORE_TYPES = ["execute_request", "execute_input", "status", "pyin"]
    STRIP_KEYS = ["execution_count", "traceback", "prompt_number"]

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
                outputs.append(self.transformMessage(msg))

        self.assertEqual(
            list(self.scrubOutputs(outputs)),
            list(self.scrubOutputs(self.cell.outputs)),
            [outputs, self.cell.outputs]
        )

    def scrubOutputs(self, outputs):
        """
        remove all scrubs from output data and text
        """
        for output in outputs:
            out = copy(output)

            for scrub, sub in self.scrubs.items():
                def _scrubLines(obj, key):
                    obj[key] = re.sub(scrub, sub, obj[key])

                if "text" in out:
                    _scrubLines(out, "text")

                if "data" in out:
                    for mime, data in out["data"].items():
                        _scrubLines(out["data"], mime)
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

    def transformMessage(self, msg):
        """
        transform a message into something like the notebook
        """
        output = {
            u"output_type": msg["msg_type"]
        }
        output.update(msg["content"])

        return self.stripKeys(output)

    def shouldContinue(self, msg):
        """
        determine whether the current message is the last for this cell
        """
        if msg is None:
            return True

        return not (msg["msg_type"] == "status" and
                    msg["content"]["execution_state"] == "idle")
