from copy import copy
import re
import unittest

from .util import Empty, isstr
from .util.dump_canonical import dump_canonical


class NoseCellTestCase(unittest.TestCase):
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
                    self.cell["outputs"][len(outputs)]
                )
                outputs.append(output)

        def _scrub(x):
            return dump_canonical(list(self.scrubOutputs(x)))

        scrubbed = _scrub(outputs)
        expected = _scrub(self.cell["outputs"])

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
        for output in cell["outputs"]:
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
