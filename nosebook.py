import logging
import os
import re
import json
from copy import copy

from unittest import TestCase

from nose.plugins import Plugin

from IPython.nbformat import read
from IPython.kernel.tests import utils

__version__ = "0.2.0"

NBFORMAT_VERSION = 4

log = logging.getLogger("nose.plugins.nosebook")


class Nosebook(Plugin):
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

    def wantFile(self, filename):
        """
        filter files to those that match nosebook-match
        """
        return self.testMatch(filename) is not None

    def loadTestsFromFile(self, filename):
        """
        find all tests in a notebook.
        """
        nb = read(filename, NBFORMAT_VERSION)

        kernel = self.newKernel(nb)

        for cell_idx, cell in enumerate(nb.cells):
            if cell.cell_type == "code":
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


class NoseCellTestCase(TestCase):
    """
    A test case for a single cell.
    """
    IGNORE_TYPES = ["execute_request", "execute_input", "status"]
    STRIP_KEYS = ["execution_count", "traceback"]

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
        self.kernel.execute(self.cell.source)

        outputs = []
        msg = None

        while self.shouldContinue(msg):
            msg = self.iopub.get_msg(block=True, timeout=1)

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
