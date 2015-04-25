import json
import unittest
import sys

from IPython import version_info

from nose.plugins import PluginTester

from nosebook import Nosebook

OTHER_ARGS = []

PY_VERSION = "py%s" % sys.version_info[0]
IPY_VERSION = "ipy%s" % version_info[0]


def match(pattern):
    return "--nosebook-match=.*/{}/{}/.*{}.*".format(
        PY_VERSION,
        IPY_VERSION,
        pattern
    )


def match_cell(pattern):
    return "--nosebook-match-cell=%s" % pattern


def scrub(patterns):
    return "--nosebook-scrub=%s" % json.dumps(patterns)


class TestNosebook(PluginTester, unittest.TestCase):
    activate = "--with-nosebook"
    plugins = [Nosebook()]
    args = [match("Test Simple"), scrub(r"<.* at 0x[0-9a-f]+>")] + OTHER_ARGS
    env = {}

    def test_found(self):
        """
        Tests are found
        """
        assert "Ran 0 tests" not in self.output, ("got: %s" % self.output)

    def test_pass(self):
        """
        Tests pass
        """
        assert "FAIL" not in self.output, ("got: %s" % self.output)

    def makeSuite(self):
        """
        will find the notebooks
        """
        pass


class TestScrubDict(TestNosebook):
    """
    Support dictionary of scrubs
    """
    args = [
        match("Scrubbing"),
        scrub({
            r"a random number <0x0\.\d*>": "scrub1",
            r"some other random number <0x0\.\d*>": "scrub2",
            r"<(.*) at 0x[0-9a-f]+>": "<\1>"
        })
    ] + OTHER_ARGS


class TestScrubList(TestNosebook):
    """
    Support list of scrubs
    """
    args = [
        match("Scrubbing"),
        scrub([
            r"a random number <0x0\.\d*>",
            r"some other random number <0x0\.\d*>",
            r"<(.*) at 0x[0-9a-f]+>"
        ])
    ] + OTHER_ARGS


class TestScrubStr(TestNosebook):
    """
    Support a single scrub
    """
    args = [
        match("Scrubbing"),
        scrub(
            r"((a|some other) random number <0x0\.\d*>)|(<.* at 0x[0-9a-f]+>)"
        )
    ] + OTHER_ARGS


class TestMatchCell(TestNosebook):
    """
    Support a normalish cell match
    """
    args = [
        match("Test"),
        match_cell(r"^\s*(class|def) .*[tT]est.*")
    ] + OTHER_ARGS


if __name__ == '__main__':
    unittest.main()
