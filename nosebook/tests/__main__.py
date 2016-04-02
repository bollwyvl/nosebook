import os
import sys

import nose


if __name__ == "__main__":
    # yuck
    os.chdir(os.path.dirname(__file__))

    sys.exit(
        nose.main(argv=["--with-coverage", "--cover-package", "nosebook"]))
