
nosebook
========

|Build Status| |PyPI| |BSD|

a `nose <http://nose.readthedocs.org/>`__ plugin for finding and running
IPython 2/3 notebooks as nose tests.

What it can't do in terms of ``setup`` and ``tearDown``, ``nosebook``
makes up for in simplicity: there is no ``%%nose`` magic, no metadata
required: the notebook on disk is the "gold master".

This makes it ideal for decreasing the burden of keeping documentation
up to date with tests by making a single set of notebooks into both
rich, multi-format documentation and a simple part of your test suite.

.. |Build Status| image:: https://travis-ci.org/bollwyvl/nosebook.svg?branch=master
   :target: https://travis-ci.org/bollwyvl/nosebook
.. |PyPI| image:: https://pypip.in/version/nosebook/badge.svg?style=flat
   :target: https://pypi.python.org/pypi/nosebook
.. |BSD| image:: https://pypip.in/license/nose-watcher/badge.svg
   :target: ./LICENSE

How does it work?
-----------------

Each notebook found according to
```nosebook-match`` <#nosebook-match>`__ is started with a fresh kernel,
based on the kernel specified in the notebook. If the kernel is not
installed, no tests will be run and the error will be logged.

Each ``code`` cell that matches
```nosebook-match-cell`` <#nosebook-match-cell>`__ will be executed
against the kernel in the order in which it appears in the notebook:
other cells e.g. ``markdown``, ``raw``, are ignored.

The number and content of outputs has to **match exactly**, with the
following parts of each output stripped:

-  execution/prompt numbers, i.e. ``[1]:``
-  tracebacks

Non-deterministic output, such as with ``_repr_`` methods that include
the memory location of the instance, will obviously not match every
time. You can use ```nosebook-scrub`` <#nosebook-scrub>`__ to rewrite or
remove offending content.

Related work
------------

-  ```ipython_nose`` <http://github.com/taavi/ipython_nose>`__ allows
   you to use a notebook as a nose runner, with traditional
   ``test_whatever`` methods. You can sort of emulate this behavior with
   ```nosebook-match-cell`` <#nosebook-match-cel>`__... as long as you
   check in passing tests!

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

    # Run against all notebooks... probably not a good idea, but maybe a great idea
    !nosetests --with-nosebook --nosebook-match .*.ipynb

``nosebook-match-cell``
^^^^^^^^^^^^^^^^^^^^^^^

A regular expression that will be replaced throughout the expected
outputs and generated outputs.

*Default: None*

.. code:: python

    # will run cells where tests are defined... but you should probably run them, too
    !nosetests --with-nosebook --nosebook-match .*Simple.* --nosebook-match-cell '(def|class).*[Tt]est'

``nosebook-scrub``
^^^^^^^^^^^^^^^^^^

A regular expression that will be replaced throughout the expected
outputs and generated outputs.

*Default: None*

.. code:: python

    # you can't fail if you don't try
    !nosetests --with-nosebook --nosebook-scrub .+

For multiple scrub values, you can pass a JSON-formatted list of regular
expressions or object of pattern-replacement pairs that will be
replaced. When passed in via the command line, you'll have to escape
special characters: using a ``.noserc`` config file makes this easier.

.. code:: python

    # there are only 10 kinds of tests...
    !nosetests --with-nosebook --nosebook-scrub='["0", "1"]'

.. code:: python

    # 0 is equally good
    !nosetests --with-nosebook --nosebook-scrub='{"\\d+": "0"}'

Contributing
------------

`Issues <https://github.com/bollwyvl/nosebook/issues>`__ and `pull
requests <https://github.com/bollwyvl/nosebook/pulls>`__ welcome!

License
-------

``nosebook`` is released as free software under the `BSD 3-Clause
license <./LICENSE>`__.
