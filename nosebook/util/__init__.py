try:
    # py3
    from queue import Empty

    def isstr(s):
        return isinstance(s, str)
except ImportError:
    # py2
    from Queue import Empty

    def isstr(s):
        return isinstance(s, basestring)  # noqa
