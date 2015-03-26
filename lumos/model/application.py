#!/usr/bin/env python
import logging
import numpy.random
import scipy.stats
from igraph import Graph, OUT as GRAPH_OUT

_logger = logging.getLogger('Application')
_logger.setLevel(logging.INFO)


class ApplicationError(Exception):
    pass


class AppDAG():
    """ An application modeled as a directed acyclic graph (DAG)

    An application is DAG of tasks/kernels.
    """
    def __init__(self, name):
        self.name = name
        self._g = Graph(directed=True)
        self._kernels = dict()
        self._node_id = 0

    def add_kernel(self, kerobj):
        node_id = self._node_id
        self._node_id += 1
        self._kernels[node_id] = kerobj
        self._g.add_vertex(name=node_id)
        return node_id

    def add_dependence(self, from_, to_):
        self._g.add_edge(from_, to_)

    def get_kernel(self, node):
        return self._kernels[node]


class Application(object):
    """ An application is a program a system runs for.

    The application has certain characteristics, such as parallel ratio
    """
    def __init__(self, f=0.9, m=0, name='app'):
        """ Initialize an application

        Args:
          f (float):
            the fraction of parallel part of program (default 0.9)
          m (float):
            the factor of memory latency (default 0)
        """
        self.f = f
        self.f_noacc = f

        self.m = m

        self.name = name

        self.kernels = dict()
        self.kernels_coverage = dict()

        self.tag = self.tag_update()

    def __repr__(self):
        return self.tag

    def tag_update(self):
        f_str = str(int((self.f-self.f_noacc)*100))

        return '-'.join([f_str, ] + [(
            '%s-%d' % (kid, int(self.kernels_coverage[kid]*100)))
            for kid in self.kernels_coverage])

    def add_kernel(self, kernel, cov):
        """Register a kernel to be accelerate.

        The kernel could be accelerated by certain ASIC, or more
        generalized GPU/FPGA

        Args:
          kernel (:class:`~lumos.model.kernel.Kernel`):
            The kernel object
          cov (float):
            The coerage of the kernel, relative to the serial execution

        Raises:
          ApplicationError:
            the given coverage (cov) is larger than the overall parallel ratio

        Returns:
          N/A
        """
        kid = kernel.kid
        if kid in self.kernels:
            _logger.warning('Kernel %s already exist' % kid)
            return False

        if cov > self.f_noacc:
            raise ApplicationError(
                '[add_kernel]: cov of {0} is too large to exceed the overall '
                'parallel ratio {1}'.format(cov, self.f_noacc))

        self.kernels[kid] = kernel
        self.kernels_coverage[kid] = cov
        self.f_noacc = self.f_noacc - cov

        self.tag = self.tag_update()

    def set_cov(self, kid, cov):
        """Set the coverage of a kernel

        Args:
          kid (str):
            The kid (name) of the kernel
          cov (float):
            The coverage of the kernel to be updated

        Raises:
          ApplicationError:
            the given coverage (cov) is larger than the overall parallel ratio

        Returns:
          N/A
        """
        if kid not in self.kernels:
            _logger.error('Kernel %s has not been registerd' % kid)
            return False

        cov_old = self.kernels_coverage[kid]

        if self.f_noacc + cov_old < cov:
            raise ApplicationError('[set_cov]: cov of {0} is too large to exceed '
                                   'the overall parallel ratio'.format(kid))

        self.kernels_coverage[kid] = cov
        self.f_noacc = self.f_noacc + cov_old - cov

        self.tag = self.tag_update()

    def get_all_kernels(self):
        """ Get all kernels within the application

        Args: N/A

        Returns:
          kernels (list): a list of names for all kernels within the application

        """
        return self.kernels.keys()

    def get_cov(self, kid):
        return self.kernels_coverage[kid]

    def get_kernel(self, kid):
        return self.kernels[kid]


# class App(object):
#     """ An application is a program a system runs for. The application has certain characteristics, such as parallel ratio """
#     def __init__(self, f=0.9, m=0, name='app'):
#         """ Initialize an application

#         Arguments:
#         f -- the fraction of parallel part of program (default 0.9)
#         m -- the factor of memory latency (default 0)

#         """
#         self.f = f
#         self.f_noacc = f

#         self.m = m

#         self.name = name

#         self.kernels = {}

#         self.tag = self.tag_update()

#     def __repr__(self):
#         return self.tag

#     def tag_update(self):
#         f_str = str(int((self.f-self.f_noacc)*100))

#         return '-'.join([f_str,] + [('%s-%d' % (kid, int(self.kernels[kid]*100))) for kid in sorted(self.kernels)])

#     def reg_kernel(self, kid, cov):
#         """Register a kernel that could be accelerated by certain ASIC, or more
#            Generalized GPU/FPGA

#         :kid: @todo
#         :cov: @todo
#         :returns: True if register succeed
#                   False if failed

#         """
#         kernels = self.kernels

#         if kid in kernels:
#             _logger.error('Kernel %s already exist' % kid)
#             return False

#         if cov > self.f_noacc:
#             _logger.error('cov {1} of kernel "{0}" is too large to exceed the overall parallel ratio {2}'.format(kid, cov, self.f_noacc))
#             return False

#         kernels[kid] = cov
#         self.f_noacc = self.f_noacc - cov

#         #self.tag = '_'.join([kid, '-'.join([str(int(100*(1-self.f))), str(int(100*(self.f_noacc))), str(int(100*cov))])])
#         self.tag = self.tag_update()

#         return True

#     def set_cov(self, kid, cov):
#         """Set the coverage of a kernel

#         :kid: @todo
#         :cov: @todo
#         :returns: @todo

#         """
#         kernels = self.kernels

#         if kid not in kernels:
#             _logger.error('Kernel %s has not been registerd' % kid)
#             return False

#         cov_old = kernels[kid]

#         if self.f_noacc + cov_old < cov:
#             _logger.error('cov of %s is too large to exceed the overall parallel ratio' % kid)
#             return False

#         kernels[kid] = cov
#         self.f_noacc = self.f_noacc + cov_old - cov

#         self.tag = self.tag_update()

#         return True

#     def get_kernel(self):
#         """Get the first kernel as kid
#         :returns: @todo

#         """
#         kids = self.kernels.keys()
#         return kids[0]

#     def get_kids(self):
#         return self.kernels.keys()

#     def get_cov(self, kid):
#         return self.kernels[kid]

#     def has_kernels(self):
#         if self.kernels:
#             return True
#         else:
#             return False

## class AppMMM(dict):
##         self["GPU"] = UCoreParam(miu=3.41,phi=0.74, bw=0.725)
##         self["FPGA"] = UCoreParam(miu=0.75,phi=0.31, bw=0.325)
##         self["ASIC"] = UCoreParam(miu=27.4,phi=0.79, bw=3.62)
##         self["O3CPU"] = UCoreParam(miu=1,phi=1, bw=0.216)
##         self["IO"] = UCoreParam(miu=1,phi=1, bw=0.16)

## class AppBS(dict):
##         self["GPU"] = UCoreParam(miu=17.0,phi=0.57, bw=5.85)
##         self["FPGA"] = UCoreParam(miu=5.68,phi=0.26, bw=3.975)
##         self["ASIC"] = UCoreParam(miu=482,phi=4.75, bw=66.249)
##         self["O3CPU"] = UCoreParam(miu=1,phi=1, bw=0.35)
##         self["IO"] = UCoreParam(miu=1,phi=1, bw=0.26)

## class AppFFT64(dict):
##         self["GPU"] = UCoreParam(miu=2.42,phi=0.59, bw = 1)
##         self["FPGA"] = UCoreParam(miu=2.81,phi=0.29, bw = 1)
##         self["ASIC"] = UCoreParam(miu=733,phi=5.34, bw = 1)
##         self["O3CPU"] = UCoreParam(miu=1,phi=1, bw=1)
##         self["IO"] = UCoreParam(miu=1,phi=1, bw=1)

# def build(cov, occ, probs, kernels, name, f_parallel=1):
#     """Build an application from a set of kernels

#     Args:
#       cov (float):
#         coverage percentage of all present kernels
#       occ (float):
#         occurance bit-vector for all kernels
#       probs (float):
#         probability vector of all kernels for appearance
#       kernels (kernel):
#         all possible kernels (kernel pool)
#       name (str):
#         the name of the application
#       f_parallel (float):
#         the fraction of parallel part

#     Returns:
#       the resulting application

#     """
#     active_kernels = dict()
#     psum = 0
#     for o,p,acc in zip(occ, probs, kernels):
#         if o:
#             active_kernels[p] = acc
#             psum = psum + p

#     ksorted = sorted(active_kernels.items())
#     krever = ksorted[:] # make another copy
#     krever.reverse()
#     app = App(f=f_parallel, name=name)

#     for (p, acc),(prv,acc2) in zip(ksorted, krever):
#         kcov = cov * prv / psum
#         #kcov = 0.05
#         app.reg_kernel(acc, kcov)

#     return app


# def build_single(cov, kernel, name, f_parallel=1):
#     app = App(f=f_parallel, name=name)
#     app.reg_kernel(kernel, cov)

#     return app


def random_uc_cov(dist, param1, param2):
    """@todo: Docstring for rand_uc_cov

    :dist: @todo
    :param1: @todo
    :param2: @todo
    :returns: @todo

    """
    if dist == 'norm':
        mean = param1
        std = param2
        r = scipy.stats.norm.rvs(mean, std)
        while r < 0:
            r = scipy.stats.norm.rvs(mean, std)
    elif dist == 'lognorm':
        mean = param1
        std = param2
        r = numpy.random.lognormal(mean, std)
    elif dist == 'uniform':
        rmin = param1
        rmax = param2
        r = numpy.random.uniform(rmin, rmax)
        while r < 0:
            r = numpy.random.uniform(rmin, rmax)
    else:
        loggging.error('Unknown distribution for coverage: %s' % dist)
        r = 0

    return r

def random_kernel_cov(cov_params):
    dist = cov_params['dist']

    if dist == 'norm':
        mean = cov_params['mean']
        std = cov_params['std']
        r = scipy.stats.norm.rvs(mean, std)
        while r < 0:
            r = scipy.stats.norm.rvs(mean, std)
    elif dist == 'lognorm':
        mean = cov_params['mean']
        std = cov_params['std']
        r = numpy.random.lognormal(mean, std)
    elif dist == 'uniform':
        rmin = cov_params['min']
        rmax = cov_params['max']
        r = numpy.random.uniform(rmin, rmax)
        while r < 0:
            r = numpy.random.uniform(rmin, rmax)
    else:
        loggging.error('Unknown distribution for coverage: %s' % dist)
        r = 0

    return r
