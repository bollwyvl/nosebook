
# nosebook
[![Build Status][svg]][status]
![pypi](https://pypip.in/version/nosebook/badge.svg?style=flat)


a [nose](http://nose.readthedocs.org/) plugin for finding and running IPython 3 notebooks as nose tests.

What it can't do in terms of `setup` and `tearDown`, `nosebook` makes up for in simplicity: there is no `%%nose` magic, no metadata required: the notebook on disk is the "gold master".

This makes it ideal for decreasing the burden of keeping documentation up to date with tests by making a single set of notebooks into both rich, multi-format documentation and a simple part of your test suite.


[svg]: https://travis-ci.org/bollwyvl/nosebook.svg?branch=master
[status]: https://travis-ci.org/bollwyvl/nosebook

## How does it work?
Each notebook found according to [`nosebook-match`](#nosebook-match) is started with a fresh kernel, based on the kernel specified in the notebook. If the kernel is not installed, no tests will be run and the error will be logged.

Each `code` cell will be executed against the kernel in the order in which it appears in the notebook: other cells e.g. `markdown`, `raw`, are ignored.

The number and content of outputs has to __match exactly__, with the following parts of each output stripped:

- execution/prompt numbers, i.e. `[1]:`
- tracebacks

Non-deterministic output, such as with `_repr_` methods that include the memory location of the instance, will obviously not match every time. You can use [`nosebook-scrub`](#nosebook-scrub) to rewrite or remove offending content.

## Related work
- [`ipython_nose`](http://github.com/taavi/ipython_nose) allows you to use a notebook as a nose runner, with traditional `test_whatever` methods.

## Configuring `nosetests` to use `nosebook`
These options can be specified in your [nose config file](./.noserc), or as long-form command line arguments, i.e. `--with-nosebook`.

#### `with-nosebook`
`nosetests` will look for notebooks that seem like tests, as configured with [`nosebook-match`](#nosebook-match). 

_Default: False_


    # Basic usage
    !nosetests --with-nosebook

#### `nosebook-match`
A regular expression that tells nosebook what should be a testable notebook.

_Default: `.*[Tt]est.*.ipynb$`_


    # Run against all notebooks... probably not a good idea
    !nosetests --with-nosebook --nosebook-match .*.ipynb

#### `nosebook-scrub`
A regular expression that will be replaced throughout the expected outputs and generated outputs.

_Default: None_


    # you can't fail if you don't try
    !nosetests --with-nosebook --nosebook-scrub .+

For multiple scrub values, you can pass a JSON-formatted list of regular expressions or object of pattern-replacement pairs that will be replaced. When passed in via the command line, you'll have to escape special characters: using a `.noserc` config file makes this easier.


    # there are only 10 kinds of tests...
    !nosetests --with-nosebook --nosebook-scrub='["0", "1"]'


    # 0 is equally good
    !nosetests --with-nosebook --nosebook-scrub='{"\\d+": "0"}'

## Contributing
[Issues](https://github.com/bollwyvl/nosebook/issues) and [pull requests](https://github.com/bollwyvl/nosebook/pulls) welcome!

## License
`nosebook` is released as free software under the [BSD 3-Clause license](./LICENSE).
