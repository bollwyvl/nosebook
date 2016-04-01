import logging

try:
    IPYTHON_VERSION = 4
    from jupyter_client.manager import start_new_kernel
    from nbformat import (
        convert as nbformat_convert,
        reads as nbformat_reads,
    )

except ImportError:
    from IPython.kernel.tests.utils import start_new_kernel

    try:
        IPYTHON_VERSION = 3
        from IPython.nbformat.converter import (
            convert as nbformat_convert,
            reads as nbformat_reads,
        )
    except ImportError:
        IPYTHON_VERSION = 2
        from IPython.nbformat.convert import (
            convert as nbformat_convert,
            reads as nbformat_reads,
        )


NBFORMAT_VERSION = 4

log = logging.getLogger(__name__)


class NosebookBase(object):
    def _readnb(self, filename):
        with open(filename) as f:
            return nbformat_reads(f.read(), NBFORMAT_VERSION)

    def readnb(self, filename):
        try:
            nb = self._readnb(filename)
        except Exception as err:
            log.info("could not be parse as a notebook %s\n%s",
                     filename,
                     err)
            return False

        return nbformat_convert(nb, NBFORMAT_VERSION)


class NosebookTwo(NosebookBase):
    """
    Implement necessary functions against the IPython 2.x API
    """

    def newKernel(self, nb):
        """
        generate a new kernel
        """
        manager, kernel = start_new_kernel()
        return kernel


class NosebookThree(NosebookBase):
    """
    Implement necessary functions against the IPython 3.x API... also
    works for 4
    """
    def newKernel(self, nb):
        """
        generate a new kernel
        """
        manager, kernel = start_new_kernel(
            kernel_name=nb.metadata.kernelspec.name
        )
        return kernel

NosebookVersion = NosebookThree

if IPYTHON_VERSION == 2:
    NosebookVersion = NosebookTwo
