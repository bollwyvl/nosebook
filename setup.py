import os
from setuptools import setup

# you'd add this, too, for `python setup.py test` integration
from setuptools.command.test import test as TestCommand


class NosebookTestCommand(TestCommand):
    def run_tests(self):
        # Run nose ensuring that argv simulates running nosetests directly
        import nose
        nose.run_exit(argv=['nosetests', '-c', './.noserc'])


def read(fname):
    """
    Utility function to read the README file.
    Used for the long_description.  It's nice, because now 1) we have a top
    level README file and 2) it's easier to type in the README file than to put
    a raw string in below ...
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="nosebook",
    version="0.1.0",
    author="Nicholas Bollweg",
    author_email="nick.bollweg@gmail.com",
    description="a nose plugin for IPython notebooks",
    license="BSD",
    keywords="IPython nose",
    url="http://github.com/bollwyvl/nosebook",
    py_modules=["nosebook"],
    long_description=read("README.md"),
    test_suite="nose.collector",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    setup_requires=[
        "nose",
        "IPython"
    ],
    entry_points={"nose.plugins.0.10": [
        "nosebook = nosebook:Nosebook",
        "subprocstreams = IPython.testing.iptest:SubprocessStreamCapturePlugin"
    ]},
    cmdclass={'test': NosebookTestCommand}
)
