import os
from setuptools import setup


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
    version="0.4.0",
    author="Nicholas Bollweg",
    author_email="nick.bollweg@gmail.com",
    description="a nose plugin for Jupyter notebooks",
    license="BSD",
    keywords="Jupyter nose notebook testing",
    url="http://github.com/bollwyvl/nosebook",
    packages=["nosebook"],
    long_description=read("README.rst"),
    test_suite="nose.collector",
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Topic :: Utilities",
        "Framework :: IPython",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Development Status :: 3 - Alpha",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: BSD License",
        "Topic :: Software Development :: Testing",
    ],
    setup_requires=[
        "IPython",
        "jupyter_client",
        "nbformat",
        "nose"
    ],
    entry_points={
        "nose.plugins.0.10": [
            "nosebook = nosebook.plugin:Nosebook",
            "subprocstreams = "
            "IPython.testing.iptest:SubprocessStreamCapturePlugin"
        ]
    }
)
