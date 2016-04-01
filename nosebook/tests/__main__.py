import os
import nose

# yuck
os.chdir(os.path.dirname(__file__))

if __name__ == "__main__":
    nose.main(argv=["--with-coverage", "--cover-package", "nosebook"])
