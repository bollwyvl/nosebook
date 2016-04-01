import json
import logging
import os
import re

from nose.plugins import Plugin

from jupyter_client.manager import start_new_kernel
import nbformat

from .util import isstr
from . import case


log = logging.getLogger(__name__)

NBFORMAT_VERSION = 4


class Nosebook(Plugin):
    """
    A nose plugin for discovering and executing Jupyter notebook cells
    as tests
    """
    name = "nosebook"

    def options(self, parser, env=None):
        """
        advertise options
        """
        if env is None:
            env = os.environ

        self.testMatchPat = env.get('NOSEBOOK_TESTMATCH',
                                    r'(?:^|[\b_\./-])[Tt]est.*\.ipynb$')

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
            return nbformat.reads(f.read(), NBFORMAT_VERSION)

    def readnb(self, filename):
        try:
            nb = self._readnb(filename)
        except Exception as err:
            log.info("could not be parse as a notebook %s\n%s",
                     filename,
                     err)
            return False

        return nbformat.convert(nb, NBFORMAT_VERSION)

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

        if nb and self.codeCells(nb):
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
                yield case.NoseCellTestCase(
                    cell,
                    cell_idx,
                    kernel,
                    filename=filename,
                    scrubs=self.scrubMatch
                )

    def newKernel(self, nb):
        manager, kernel = start_new_kernel(
            kernel_name=nb.metadata.kernelspec.name
        )
        return kernel
