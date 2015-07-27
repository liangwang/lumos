import lxml.etree as etree
from .kernel import Kernel, KernelParam, KernelError
from .kernel import load_suite_xmlfile as load_kernels_xmlfile
from .kernel import load_suite_xmltree as load_kernels_xmltree
from .application import SimpleApp, DetailedApp, LinearApp, DAGApp
from .application import load_suite_xmlfile as load_apps_xmlfile
from .application import load_suite_xmltree as load_apps_xmltree


def load_kernels_and_apps(xmlfile):
    """Load kernels and applications from an XML file.

    Parameters
    ----------
    xmlfile : filepath
      The file to be loaded, in XML format. The suite includes two
      section: kernels and applications.

    Returns
    -------
    kernels : dict
      A dict of (kernel_name, kernel_object) pair, indexed by kernel's name.
    applications : dict
      A dict of (application_name, applicatin_object) pair, indexed by
      application's name.

    Raises
    ------
    KernelError: if parameters is not float

    """
    tree = etree.parse(xmlfile)

    ktree = tree.find('kernels')
    if ktree is None:
        print('No kernels')
        return None, None
    kernels = load_kernels_xmltree(ktree)

    atree = tree.find('apps')
    if atree is None:
        print('No applications')
        return None, None
    applications = load_apps_xmltree(atree, kernels)

    return kernels, applications
