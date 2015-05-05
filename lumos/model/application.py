#!/usr/bin/env python
import abc
import logging
import numpy.random
import scipy.stats
from igraph import Graph, IN as GRAPH_IN

_logger = logging.getLogger('Application')
_logger.setLevel(logging.INFO)


class AppDAGError(Exception):
    pass


class AppBase():
    __metaclass__ = abc.ABCMeta

    def __init__(self, name_, type_):
        self._name = name_
        self._type = type_

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @classmethod
    @abc.abstractmethod
    def load_app_from_xml(cls, xmltree, kernels):
        return


def load_app_from_xml(xmltree, kernels):
    type_ = xmltree.get('type')
    if not type:
        raise AppDAGError('No type attribute found in XML tree')

    if type_ == 'linear':
        return AppLinear.load_app_from_xml(xmltree, kernels)
    elif type_ == 'dag':
        return AppDAG.load_app_from_xml(xmltree, kernels)
    elif type_ == 'spread':
        return AppSpread.load_app_from_xml(xmltree, kernels)
    else:
        raise AppDAGError('Unknown app type {0}'.format(type_))


class AppLinear(AppBase):
    def __init__(self, name):
        self._name = name
        self._kernels = dict()
        self.length = dict()
        self._num_kernels = 0

        super(AppLinear, self).__init__(name, 'linear')

    @classmethod
    def load_app_from_xmltree(cls, xmltree, kernels):
        pass


class AppSpread(AppBase):
    def __init__(self, name):
        super(AppSpread, self).__init__(name, 'spread')


class AppDAG(AppBase):
    """An application modeled as a directed acyclic graph (DAG)

    An application is DAG of tasks/kernels. Kernels are referred by a
    handler, called `kernel index`. Internally, the kernel index is the
    node index in the DAG (represented using `igraph` library).

    Attributes
    ----------
    name : str, read-only
      The name of an application
    """
    def __init__(self, name):
        self._g = Graph(directed=True)
        self._kernels = dict()
        self._length = dict()
        self._max_depth = -1
        self._num_kernels = 0

        super(AppDAG, self).__init__(name, 'dag')

    @classmethod
    def load_apps_from_xmltree(cls, xmltree, kernels):
        """load applications from an XML tree node

        Parameters
        ----------
        xmltree : :class:`~lxml.etree.Element`
          root node of the XML tree
        kernels : dict
          kernels dict indexed by kernel name

        Returns
        -------
        dict
          application dict indexed by application's name
        """
        applications = dict()
        for r_ in xmltree:
            a = cls.load_app_from_xmltree(r_, kernels)
            applications[a.name] = a
        return applications

    @classmethod
    def load_app_from_xmltree(cls, xmltree, kernels):
        name = xmltree.get('name')
        if not name:
            raise AppDAGError('No name attribute found in XML tree')
        a = cls(name)

        ks = xmltree.find('kernel_config')
        if ks is None:
            raise AppDAGError('No kernel configs found in XML tree')

        for ele in ks:
            val_ = ele.get('index')
            if not val_:
                raise AppDAGError('No kernel index in kernel config')
            node_id = int(val_)

            k_name = ele.get('name')
            if not k_name:
                raise AppDAGError('no kernel name in kernel config')

            val_ = ele.get('cov')
            if not val_:
                raise AppDAGError('No kernel length in kernel config')
            k_cov = float(val_)

            k_preds = ele.get('pred')
            if not k_preds:
                k_preds = 'None'

            kernel_idx = a._add_kernel(kernels[k_name], k_cov)
            if kernel_idx != node_id:
                raise AppDAGError(
                    "kernel index mismatch with AppDAG.add_kernel."
                    " Probably because the kernel is not specified in order in the XML tree.")
            if k_preds != 'None':
                preds = [int(i) for i in k_preds.split(',')]
                for _ in preds:
                    a._add_dependence(_, kernel_idx)
        a._prep_baseline()
        return a

    @property
    def depth(self):
        return self._max_depth

    def get_all_kernel_lengths(self):
        return [self._length[idx_] for idx_ in self._g.vs.indices]

    def get_kernel_length(self, kernel_idx):
        """Get the length of a kernel, indicated by kernel_idx

        Parameters
        ----------
        kernel_idx : int
          The kernel index.

        Returns
        -------
        float
          the length of the kernel
        """
        return self._length[kernel_idx]

    def _add_kernel(self, kerobj, len_):
        """Add a kernel into application.

        Parameters
        ----------
        kerobj : :class:`~lumos.model.Kernel`
          The kernel object to be added
        len_ : float
          The run length of a kernel executed on a single base line core
          (BCE).

        Returns
        -------
        int
          kernel index
        """
        kernel_idx = self._g.vcount()
        self._g.add_vertex(name=kerobj.name, depth=1)
        self._kernels[kernel_idx] = kerobj
        self._length[kernel_idx] = len_
        self._num_kernels += 1
        return kernel_idx

    def _add_dependence(self, from_, to_):
        """Add kernel dependence between two kernels.

        Parameters
        ----------
        from\_, to\_: kernel index
          Precedent kernel (from\_) and the dependent kernel (to\_)
          expressed by kernel index
        """
        self._g.add_edge(from_, to_)
        self._g.vs[to_]['depth'] = max(self._g.vs[from_]['depth'] + 1,
                                       self._g.vs[to_]['depth'])
        self._max_depth = max(self._g.vs[to_]['depth'], self._max_depth)

    def get_all_kernels(self, mode='index'):
        """get all kernels

        Parameters
        ----------
        mode : str
          The mode of return value. It could be either 'index' or
          'object'. If 'index', kernel indexes will be returned. If
          'object', kernel objects will be returned.

        Returns
        -------
        list
          Depending on `mode` parameter.
        """
        if mode == 'object':
            return [self._kernels[idx_] for idx_ in self._g.vs.indices]
        else:
            return self._g.vs.indices

    def get_kernel(self, kernel_idx):
        """Get the kernel object

        Parameters
        ----------
        kernel_idx : int
          The kernel index

        Returns
        -------
        :class:`~lumos.model.Kernel`
          The kernel object.
        """
        return self._kernels[kernel_idx]

    def _prep_baseline(self):
        self._depth_sorted = [[v_.index for v_ in self._g.vs.select(depth_eq=d_)]
                              for d_ in range(1, self._max_depth+1)]
        finish_time = dict.fromkeys(self._g.vs.indices, 0)
        for l, node_list in enumerate(self._depth_sorted):
            if l == 0:
                for node in node_list:
                    finish_time[node] = self._length[node]
            else:
                for node in node_list:
                    start = max([finish_time[n_]
                                 for n_ in self._g.neighbors(node, mode=GRAPH_IN)])
                    finish_time[node] = start + self._length[node]
        self._baseline_runtime = max(finish_time.values())

    def get_kernel_depth(self, kernel_idx):
        return self._g.vs[kernel_idx]['depth']

    def get_all_kernel_depth(self):
        return self._g.vs['depth']

    def kernels_topo_sort(self):
        """sort kernels in a topological order.

        Returns
        -------
        list
          kernel indexes in a topological sort order
        """
        return self._g.topological_sorting()

    def get_precedent_kernel(self, kernel_idx):
        """Get the precedent (pre-requisite) kernels.

        Returns
        -------
        list
          A list of kernel indexes that precedent the given kernel. None
          if no precedent kernels exist, e.g. the starting kernel.
        """
        return self._g.neighbors(kernel_idx, mode=GRAPH_IN)

    def kernels_depth_sort(self):
        """sort kernels by their depth.

        Returns
        -------
        list
          kernel indexes grouped by its depth in the DAG. An example output looks
          like::

            [
               [0,1],   # depth == 0
               [2,3,4], # depth == 1
               [5,6],   # depth == 2
            ]
        """
        try:
            return self._depth_sorted
        except AttributeError:
            raise AppDAGError('App not initiliazed properly')

    def get_speedup(self, speedup_dict):
        """Get the speedup of an application by given a speedup vector of each kernel.

        Parameters
        ----------
        speedup_dict : dict
          provides speedup indexed by kernel index, an example of
          speedup_dict would be::

            {
              0: 1.2, # kernel 0 has speedup of 1.2x, or a run time of 1/1.2
              1: 0.8, # kernel 1 has speedup of 0.8x, and this is actually a slowdown
            }

          kernels not specified will be assumed to have a speedup of 1x,
          e.g. not speedup
        """
        speedups = [speedup_dict[idx_] if idx_ in speedup_dict else 1
                    for idx_ in self._g.vs.indices]
        kernel_runtime = [self._length[idx_]/speedups[idx_]
                          for idx_ in self._g.vs.indices]
        finish_time = dict.fromkeys(self._g.vs.indices, 0)
        for l, node_list in enumerate(self._depth_sorted):
            if l == 0:
                for node in node_list:
                    finish_time[node] = kernel_runtime[node]
            else:
                for node in node_list:
                    start = max([finish_time[n_]
                                for n_ in self._g.neighbors(node, mode=GRAPH_IN)])
                    finish_time[node] = start + kernel_runtime[node]
        app_runtime = max(finish_time.values())
        return self._baseline_runtime / app_runtime


class ApplicationError(Exception):
    pass


class SimpleApplication(object):
    """ A simple application is an abstract program partitioned into serial and
    parallel portions.

    In this abstrace model, a program(application) is partitioned ideally into
    the serial and parallel sections. The serial sections can only be executed
    on a single core, but not accelerators (may be extended to execute the
    serial section with accelerators as well in the future). The parallel
    section can be perfectly parllelized on multiple cores, e.g. the throughput
    improvment is linear to the number of cores. Besides, the parallel section
    can also be accelerated by accelerators for better performance and/or energy
    efficiency.


    Attributes
    ----------
    f: float, in the range of [0, 1]
      the fraction of parallel section.
    name: str
      the name (id) of the application
    """
    def __init__(self, f=0.9, m=0, name='app'):
        """ Initialize an application

        Parameters
        ----------
        f : float
          the fraction of parallel part of program (default 0.9)
        m : float, optional
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
            '%s-%d' % (name, int(self.kernels_coverage[name]*100)))
            for name in self.kernels_coverage])

    def add_kernel(self, kernel, cov):
        """Register a kernel to be accelerate.

        The kernel could be accelerated by certain ASIC, or more
        generalized GPU/FPGA

        Parameters
        ----------
        kernel : :class:`~lumos.model.kernel.Kernel`
          The kernel object
        cov : float
          The coerage of the kernel, relative to the serial execution

        Raises
        ------
        ApplicationError
          the given coverage (cov) is larger than the overall parallel ratio

        """
        name = kernel.name
        if name in self.kernels:
            _logger.warning('Kernel %s already exist' % name)
            return False

        if cov > self.f_noacc:
            raise ApplicationError(
                '[add_kernel]: cov of {0} is too large to exceed the overall '
                'parallel ratio {1}'.format(cov, self.f_noacc))

        self.kernels[name] = kernel
        self.kernels_coverage[name] = cov
        self.f_noacc = self.f_noacc - cov

        self.tag = self.tag_update()

    def set_cov(self, name, cov):
        """Set the coverage of a kernel

        Parameters
        ----------
        name : str
          The name of the kernel
        cov : float
          The coverage of the kernel to be updated

        Raises
        ------
        ApplicationError
          the given coverage (cov) is larger than the overall parallel ratio

        """
        if name not in self.kernels:
            _logger.error('Kernel %s has not been registerd' % name)
            return False

        cov_old = self.kernels_coverage[name]

        if self.f_noacc + cov_old < cov:
            raise ApplicationError('[set_cov]: cov of {0} is too large to exceed '
                                   'the overall parallel ratio'.format(name))

        self.kernels_coverage[name] = cov
        self.f_noacc = self.f_noacc + cov_old - cov

        self.tag = self.tag_update()

    def get_all_kernels(self):
        """ Get all kernels within the application

        Returns
        -------
        list
          a list of names for all kernels within the application

        """
        return self.kernels.keys()

    def get_cov(self, name):
        return self.kernels_coverage[name]

    def get_kernel(self, name):
        return self.kernels[name]
