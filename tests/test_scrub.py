import nosebook
import munch

import unittest


class TestNosebook(unittest.TestCase):
    def setUp(self):
        self.cell = munch.Munch({
            "cell_type": "code",
            "execution_count": 21,
            "metadata": {
                "collapsed": False
            },
            "outputs": [
                {
                    "name": "stdout",
                    "output_type": "stream",
                    "text": [
                        "a random number <0x0.17537838216771606>\n",
                        "1234\n"
                    ]
                },
                {
                    "data": {
                        "text/plain": [
                            "'a random number <0x0.17537838216771606>'"
                        ]
                    },
                    "execution_count": 21,
                    "metadata": {},
                    "output_type": "execute_result"
                }
            ],
            "source": [
                "print(rnd)\n",
                "print(1234)\n",
                "rnd"
            ]
        })

        self.kernel = munch.Munch({
            "iopub_channel": {}
        })

    def make_case(self, scrubs, expected):
        case = nosebook.NoseCellTestCase(
            self.cell,
            0,
            self.kernel,
            scrubs=scrubs
        )

        self.assertEquals(
            list(case.scrubOutputs(self.cell.outputs)),
            expected,
            list(case.scrubOutputs(self.cell.outputs)),
        )

    def test_scrub_dict(self):
        self.make_case(
            {
                r"a random number <0x0\.\d*>": "scrub1",
                r"some other random number <0x0\.\d*>": "scrub2",
                r"<(.*) at 0x[0-9a-f]+>": "<\1>"
            },
            [
                {
                    'output_type': 'stream',
                    'name': 'stdout',
                    'text': ['scrub1\n', '1234\n']
                },
                {
                    'metadata': {},
                    'output_type': 'execute_result',
                    'data': {
                        'text/plain': ["'scrub1'"]
                    }
                }
            ]
        )

    def test_scrub_list(self):
        self.make_case(
            {
                r"a random number <0x0\.\d*>": "scrub1",
                r"some other random number <0x0\.\d*>": "scrub2",
                r"<(.*) at 0x[0-9a-f]+>": "scrub3"
            },
            [
                {
                    'output_type': 'stream',
                    'name': 'stdout',
                    'text': ['scrub1\n', '1234\n']
                },
                {
                    'output_type': 'execute_result',
                    'data': {
                        'text/plain': ["'scrub1'"]
                    },
                    'metadata': {}
                }
            ]
        )

    def test_scrub_str(self):
        self.make_case(
            {
                r"((a|some other) random number <0x0\.\d*>)|"
                r"<(.*) at 0x[0-9a-f]+>": "<scrub1>"
            },
            [
                {
                    'output_type': 'stream',
                    'name': 'stdout',
                    'text': ['<scrub1>\n', '1234\n']
                }, {
                    'output_type': 'execute_result',
                    'data': {
                        'text/plain': ["'<scrub1>'"]
                    }, 'metadata': {}
                }
            ]
        )
