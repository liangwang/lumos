.. Lumos documentation master file, created by
   sphinx-quickstart on Thu Feb 14 10:20:41 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=================
 Lumos Framework
=================

.. toctree::
   :maxdepth: 2


Introduction
============

Lumos is a framework to analytically quantify the performance limits
of many-core, heterogeneous systems operating at low supply voltage
(e.g. near-threshold). Due to limited scaling of supply voltage, power
density is expected to grow in future technology nodes. This
increasing power density potentially limits the number of transistors
switching at full speed in the future. Near-threshold operation can
increase the number of simultaneously active cores, at the expense of
much lower operating frequency ("dim silicon"). Although promising
to increase overall throughput, dim cores suffer from diminishing
returns as the number of cores increases. At this point, hardware
accelerators become more efficient alternatives. Lumos is developed to
explore such a broad design space.

How to Get it
=============

The latest Lumos can be downloaded from `tar.gz
<https://github.com/liangwang/lumos/archive/latest.tar.gz>`_ or `zip
<https://github.com/liangwang/lumos/archive/latest.zip>`_. Source code is
available for quick browse at `here <https://github.com/liangwang/lumos/tree/latest>`_.

Quick Start
===========

Lumos is written mostly in Python, with external modules written in C. The
latest Lumos requires python 3.4 and a recent GCC, and has been tested on
Ubuntu-14.04 box with python 3.4.3 and gcc-4.8.

Prepare python modules
----------------------

* numpy and scipy

  This is usually included in a typical installation of python. In
  case you do not have it, these two packages can be found at `numpy
  <http://www.numpy.org>`_ and `scipy <http://www.scipy.org>`_. Lumos
  has been tested on numpy-1.6.1 and scipy-0.9.0

* pandas

  This package is used to process technology model files.

* matplotlib

  This package is required to generate plots for analyses. It is
  usually included in the package repositories of popular Linux
  distributions (e.g. Ubuntu). Otherwise, you can always get it from
  `matplotlib <http://matplotlib.org>`_. Lumos has been tested on
  matplotlib-1.1.1rc.


* lxml

  This package is required to parse the descriptions of kernels and
  workloads stored in xml files. It is included in the package
  repository of Ubuntu, and can also be downloaded at `lxml
  <http://lxml.de/index.html#download>`_. Lumos has been tested on
  lxml-2.3.2.

* ConfigObj

  This package is required to parse configurations. It can be installed using
  ``pip`` as::

    pip install configobj

* python-igraph

  This package is required to model directed acyclic graph based
  application model. It can be installed using ``pip`` as::

    pip install python-igraph

  .. note:: If igraph C-library is not installed (on Ubuntu, it could be
            installed by ``pip install libigraph libigraph-dev``), the above
            procedure will try to compile the library first. In this case, GCC
            is required.

* nose (optional)

  This packages is only required for unit test.

Build cacti-p
-------------

This is as simple as running the following command in the home directory of Lumos::

  make -C cacti-p

Run simple example
------------------
Now it is ready to go. Since it is purely pythonic, Lumos does not
need any compilation steps (technically speaking, the interpreter will
"compile" all python scripts to accelerate execution, but this is all
transparent to users). Just follow these steps:

1. Set environment variable ``LUMOS_HOME`` to root directory of the
   package::

   >cd Lumos-0.1
   >export LUMOS_HOME=(full-path-to)/Lumos-0.1

2. Run the sample analysis::

   >python lumos/analyses/homosys_example.py

3. Done!

Now the plots for this sample analysis should be ready to check out in
``$LUMOS_HOME/analyses/core/figures``.

Model
=====

The model includes technology model, cores, accelerators, and applications.

Technology
----------

.. highlight:: python
   
The supported technology libraries are:

+---------+-------------+---------------+
|TechName | TechVariant | Mnemonic      |
+=========+=============+===============+
|         |    hp       |  cmos-hp      |
|  cmos   +-------------+---------------+
|         |    lp       |  cmos-lp      |
+---------+-------------+---------------+
|         |    hp       |  finfet-hp    |
|  finfet +-------------+---------------+
|         |    lp       |  finfet-lp    |
+---------+-------------+---------------+
|         |  homo30nm   |  tfet-homo30nm|
|  tfet   +-------------+---------------+
|         |  homo60nm   |  tfet-homo60nm|
+---------+-------------+---------------+

Lumos provides a factory generator to retrieve supported technologies by the
name and variant of a technology model::

  from lumos.model.tech import get_model
  techmodel = get_model('cmos', 'hp')

Core
----

To create an object for conventional cores, these four arguments have to be specified:

- technology node (nm)
- technology name
- technology variant
- core type

For example, the following code snippet create an in-order core using CMOS technology with hp variant at 45nm::

  from lumos.model.core import BaseCore
  core = BaseCore(45, 'cmos', 'hp', 'io')

All supported combinations are listed as follows:

+----------+--------------------+----------------------------+-------------------+
| TechName | TechVariant        | CoreType                   | TechNode (nm)     |
+==========+====================+============================+===================+
| cmos     | hp, lp             | io, o3                     | 45, 32, 22, 16    |
+----------+--------------------+----------------------------+-------------------+
| finfet   | hp, lp             | smallcore, bigcore         | 20, 16, 14, 10, 7 |
+----------+--------------------+----------------------------+-------------------+
| tfet     | homo30nm, homo60nm | io, o3, smallcore, bigcore | 22                |
+----------+--------------------+----------------------------+-------------------+


Accelerators
------------

To be edited

Application
-----------

Sirius-suite
~~~~~~~~~~~~

Data extracted from table 5 of the paper [sirius-asplos15]_:

.. [sirius-asplos15] Sirius: An Open End-to-End Voice and Vision Personal
                     Assistant and Its Implications for Future Warehouse Scale
                     Computers, ASPLOS 15.

.. [ucore-micro10] Single-Chip Heterogeneous Computing: Does the Future Include
                   Custom Logic, FPGAs, and GPGPUs?, MICRO 10

.. _SPECfp2006 Core i7-960: https://www.spec.org/cpu2006/results/res2011q3/cpu2006-20110718-17508.html 

.. _SPECfp2006 Xeon E3-1240 v3: https://www.spec.org/cpu2006/results/res2014q2/cpu2006-20140407-29280.html

.. _Virtex6 ML605: http://www.xilinx.com/products/boards-and-kits/ek-v6-ml605-g.html

.. _Virtex6 LXT FPGA Datasheet: http://www.xilinx.com/publications/prod_mktg/Virtex6_Product_Table.pdf

.. _Sirius: http://sirius.clarity-lab.org/


The paper reported speedup achieved by FPGA (Xilinx ML605) compared to
conventional CPU (Xeon E3-1240 v3). We scale the performance speedup as if the
baseline is a Core i7-960 using SPECfp2006 scores. According to `SPECfp2006 Core
i7-960`_ and `SPECfp2006 Xeon E3-1240 v3`_, the SPECfp2006 scores are 43.5 and
75.6, respectively. Therefore, speedup numbers in table 5 of [sirius-asplos15]_
are scaled by a factor of 75.6/43.5 = 1.738 for FPGA accelerator. Further, the
area of FPGA is estimated by assuming each LUT takes 0.00191mm2 at 40nm. The
total number of LUT for Virtex6 LXT240T is 37680*8. The resource utilization of
each kernel are listed as follows:

- gmm: 100%
- dnn-asr: 100%
- stemmer: 100%
- regex: 100%
- crf: 10 %
- fe: 20%
- fd: 20%

Analysis
========

A typical analysis in the Lumos framework involves three steps: define the
worload, define the system, do analysis.

Define Workload
---------------

.. highlight:: xml

The workload in the Lumos framework is defined as a pool of applications. Each
single application is divided into serial and parallel parts, and the ratio is
specified as ``f_parallel``. Part of an application can be also partitioned into
several computing kernels. These kernels can be accelerated by various computing
units, such as multicore, possibly dim CPU cores, RL, and customized ASIC. We
model the speedup and the power consumption of RL and customized ASIC for a
given kernel by u-core parameters.

A workload is defined by enumerating all applications in the format of XML, such
as::

       <workload>
          <app name="app0">
            <f_parallel>1</f_parallel>
            <kernel_config>
              <kernel name="ker005" cov="0.4826"/>
            </kernel_config>
          </app>
          ...
       </workload>

where ``f_parallel`` is the parallel ratio. Within ``kernel_config``, the
``name`` is the name of the kernel, and ``cov`` is the kernel's execution time
in percentage to the application running with a single baseline core (e.g. an
in-order core at the nominal supply voltage and 45nm). Coverages of kernels are
not necessarily summed to 100%. Lumos will assume the rest of application can
not be accelerated and only be executed on conventional cores.

A set of kernels is enumerated in the format of XML as well, such
as::

       <kernels>
         <kernel name="ker005">
	   <fpga miu="20"/>
	   <asic miu="100"/>
	   <occur>0.003206</occur>
	 </kernel>
	 ...
       </kernels>

Where ``miu`` is the relative performance for FPGA and ASIC,
respectively. ``occur`` is the probability of this kernel to be
presented in an application.

There are a couple of helper functions to assist you in generating kernels and
applications following certain statistical distributions. See
:func:`~lumos.model.kernel.create_fixednorm_xml`,
:func:`~lumos.model.kernel.create_randnorm_xml`,
:func:`~lumos.model.workload.build`,
:func:`~lumos.model.workload.build_fixedcov` for more details. Moreover,
existing XML descriptions can be loaded by :func:`~lumos.model.kernel.load_xml`
for kernels and :func:`~lumos.model.workload.load_xml` for workloads.

Define System
-------------

Lumos supports conventional cores such as a Niagara2-like in-order core and an
out-or-order core (:class:`~lumos.model.core.IOCore` and
:class:`~lumos.model.core.O3Core`), as well as un-conventional cores, such as
accelerators (:class:`~lumos.model.ucore.UCore`), and federated cores
(:class:`~lumos.model.fedcore.FedCore`).

On top of these cores, Lumos supports two kinds of systems: a homogeneous
multi-core system (:class:`~lumos.model.system.HomogSys`), and a heterogeneous
multi-core system with a serial core and certain amount of throughput cores, as
well as accelerators (:class:`~lumos.model.system.HeterogSys`). The usage of
these two systems are demonstrated later in Example Analysis section.


Do Analysis
-----------

:class:`~lumos.model.system.HeterogSys` provides a method
:func:`~lumos.model.system.HeterogSys.get_perf` to get the relative
performance of the system for a given application.

:class:`~lumos.model.system.HomogSys` provides a couple of methods to retrieve
relative performance of system for a given application:

* Explicit constraint on the supply voltage.

  In this case, the system will try to enable as many cores at the given supply
  as possible within the given power budget. If the supply voltage is relatively
  high, it ends up with a dark silicon homogeneous many-core system. Use
  :func:`~lumos.model.system.HomogSys.perf_by_vfs` and
  :func:`~lumos.model.system.HomogSys.perf_by_vdd` for this scenario.

* Explicit constraint on the number of active cores.

  In this case, the system will probe for the highest supply voltage for the
  core to meet the overall power budget. Use
  :func:`~lumos.model.system.HomogSys.perf_by_cnum` for this scenario.

* No constraints on the supply voltage or the number of active cores,

  In this case, the system will probe for the optimal configuration of supply
  voltage and the number of cores to achieve the best overall throughput. Use
  :func:`~lumos.model.system.HomogSys.opt_core_num` for this scenario.


Example Analyses
----------------

.. highlight:: python

1. Example of using :class:`~lumos.model.system.HomogSys`

   An example analysis of :class:`~lumos.model.system.HomogSys` is in
   ``$LUMOS_HOME/lumos/analyses/homosys_example.py``. This example models a
   homogeneous many-core architecture composed of Niagara2-like in-order cores.
   The system is defined as follow::

       sys = HomogSys()
       sys.set_sys_prop(area=self.sys_area, power=self.sys_power)
       sys.set_sys_prop(core=IOCore(mech=self.mech))


   The analysis compares four scenarios applied to the system: 1) dim cores
   without consideration of variation-induced frequency penalty; 2) dim
   cores considering the frequency penalty; 3) dim cores with reduced
   frequency penalty of 0.5 and 0.1 respectively; 4) dark cores with maximum
   supply voltage (1.3x nominal) and frequency. Each scenario will require some
   tweaks to system parameters, for example, the second scenario requires::

       sys.set_core_prop(tech=ctech, pv=True)


   More details can be found in
   :func:`~lumos.analyses.homosys_example.HomosysExample.analyze`. For each
   scenario, the relative performance is obtained by
   :func:`~lumos.model.system.HomogSys.opt_core_num` as follow::

       ret = sys.opt_core_num()
       ret['perf']


   Finally, :func:`~lumos.analyses.analysis.plot_series` is used to generate a
   plot for the above scenarios, as in
   :func:`~lumos.analyses.homosys_example.HomosysExample.plot`.


2. Example of using :class:`~lumos.model.system.HeterogSys`

   An example analysis of :class:`~lumos.model.system.HeterogSys` is in
   ``$LUMOS_HOME/lumos/analyses/heterosys_example.py``. This example models a
   heterogeneous many-core system composed of in-order cores, reconfigurable
   logic (FPGA), and dedicated ASICs. All related files for this analysis are
   placed in ``$LUMOS_HOME/analyses/heterosys_example``. For maximum flexibility,
   this example employs an external configuration file to specify various input
   parameters in addition to command line parameters. The default configurations
   file is ``heterosys_example.cfg``. This example uses pre-defined synthetic
   kernels and workloads stored in ``kernels_asicfpgaratio10x.xml`` and
   ``workload_norm40x10.xml``. The analysis will load kernels and the workload as
   follows::

       kernels = kernel.load_xml(options.kernel)
       workload = workload.load_xml(options.workload)

   The system is defined as follow::

       sys = HeterogSys(self.budget)
       sys.set_mech('HKMGS')
       sys.set_tech(16)
       if kfirst != 0:  # there are ASIC accelerators to be added
           sys.set_asic('_gen_fixednorm_004', alloc*kfirst*0.33)
           sys.set_asic('_gen_fixednorm_005', alloc*kfirst*0.33)
           sys.set_asic('_gen_fixednorm_006', alloc*kfirst*0.34)
       sys.realloc_gpacc(alloc*(1-kfirst))
       sys.use_gpacc = True

   The performance is collected as follows::

       perfs = numpy.array([ sys.get_perf(app)['perf']
                   for app in self.workload])

   This analysis involves a large design space exploration. To accelerate the
   exhaustive search, this analysis also takes advantage of parallel execution
   to run fast on multicore machines.

   Finally, the analysis is plotted in
   :func:`~lumos.analyses.heterosys_example.HeterosysExample.plot`.

3. More examples.

   There are a lot of analyses in ``$LUMOS_HOME/lumos/analyses``, which can be
   used as examples of various functions the Lumos framework provides.
   Unfortunately, they are less documented at this moment.

License
=======

.. include:: ../LICENSE
   :literal:
   
Funding Acknowledgement
=======================

This work was supported by the SRC under GRC task 1972.001 and the NSF under grants MCDA-0903471 
and CNS-0916908 and byDARPA MTO under contract HR0011-13-C-0022 and by NSF grant no. EF-1124931
and C-FAR, one of six centers of STARnet, a Semiconductor Research Corporation program sponsored 
by MARCO and DARPA. The views expressed are those of the authors and do not reﬂect the ofﬁcial 
policy or position of the sponsors.

