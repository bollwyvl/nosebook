
nosebook
========

a `nose <http://nose.readthedocs.org/>`__ plugin for finding and running
IPython 3 notebooks as nose tests.

You can use it to decrease the burden of documentation and testing by
making a single set of notebooks into both rich documentation and a part
of your test suite, with certain limitations.

|Build Status|

.. |Build Status| image:: https://travis-ci.org/bollwyvl/nosebook.svg?branch=master
   :target: https://travis-ci.org/bollwyvl/nosebook

How does it work?
-----------------

Each notebook is started with a fresh kernel, based on the kernel
specified in the notebook. If the kernel is not installed, no tests will
be run and the error will be logged.

Each ``code`` will be executed against the kernel in the order they
appear in the notebook: other cells e.g. ``markdown``, ``raw``, are just
ignored.

The output has to **match exactly**, with the following parts of the
output stripped:

-  execution numbers, i.e. ``[1]:``
-  tracebacks

This can be a problem, such as with class ``_repr_`` methods that
include the memory location of the instance, so care should be taken
with non-deterministic output.

Configuring ``nosetests`` to use ``nosebook``
---------------------------------------------

These options can be specified in your `nose config file <./.noserc>`__,
or as long-form command line arguments, i.e. ``--with-nosebook``.

``with-nosebook``
^^^^^^^^^^^^^^^^^

``nosetests`` will look for notebooks that seem like tests, as
configured with ```nosebook-match`` <#nosebook-match>`__.

*Default: False*

.. code:: python

    # Basic usage
    !nosetests --with-nosebook
``nosebook-match``
^^^^^^^^^^^^^^^^^^

A regular expression that tells nosebook what should be a testable
notebook.

*Default: ``.*[Tt]est.*.ipynb$``*

.. code:: python

    # Run against all notebooks... probably not a good idea
    !nosetests --with-nosebook --nosebook-match .*.ipynb
``python setup.py test`` integration
------------------------------------

Strangely complex, see the example in ```setup.py`` <./setup.py>`__.
