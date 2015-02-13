import logging
import os
import re

from unittest import TestCase

from nose.plugins import Plugin

from IPython.nbformat import read
from IPython.kernel.tests import utils


NBFORMAT_VERSION = 4

log = logging.getLogger("nose.plugins.nosebook")


class Nosebook(Plugin):
    name = "nosebook"

    def options(self, parser, env=os.environ):
        super(Nosebook, self).options(parser, env=env)

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

    def configure(self, options, conf):
        super(Nosebook, self).configure(options, conf)
        self.testMatch = re.compile(options.nosebookTestMatch).match

    def wantFile(self, filename):
        return self.testMatch(filename) is not None

    def loadTestsFromFile(self, filename):
        nb = read(filename, NBFORMAT_VERSION)

        kernel = self.newKernel(nb)

        for cell in nb.cells:
            if cell.cell_type == "code":
                yield NoseCellTestCase(cell, kernel)

    def newKernel(self, nb):
        # use a new kernel per file
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

    def __init__(self, cell, kernel, *args, **kwargs):
        super(NoseCellTestCase, self).__init__(*args, **kwargs)
        self.cell = self.sanitizeCell(cell)

        self.kernel = kernel
        self.iopub = self.kernel.iopub_channel

    def runTest(self):
        self.kernel.execute(self.cell.source)

        outputs = []
        msg = None

        while self.shouldContinue(msg):
            msg = self.iopub.get_msg(block=True, timeout=1)

            if msg["msg_type"] not in self.IGNORE_TYPES:
                outputs.append(self.transformMessage(msg))

        if not self.cell.outputs:
            self.assertEqual(outputs, [])
        else:
            self.assertEqual(outputs, self.cell.outputs)

    def stripKeys(self, d):
        for key in self.STRIP_KEYS:
            d.pop(key, None)
        return d

    def sanitizeCell(self, cell):
        # remove non-reproducible things
        for output in cell.outputs:
            self.stripKeys(output)
        return cell

    def transformMessage(self, msg):
        # transform a message into something like the notebook
        output = {
            u"output_type": msg["msg_type"]
        }
        output.update(msg["content"])

        return self.stripKeys(output)

    def shouldContinue(self, msg):
        if msg is None:
            return True

        return not (msg["msg_type"] == "status" and
                    msg["content"]["execution_state"] == "idle")
