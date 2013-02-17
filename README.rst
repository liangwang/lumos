=============================================================================
Lumos: A model for heterogeneous many-core system operating at near-threshold
=============================================================================

About
=====

An analytical model written in Python, to study the performance of dim silicon.
Check out the `document <http://liangwang.github.com/lumox>`_ for more details.

Directory Hierarchy
===================

* analyses

  This is the root directory for analysis-related files, such as configurations,
  kernel/workload definitions, intermediate data files, and figures. Each
  analysis has its own directory as the working place under this directory.

* data
  This directory holds auxiliary data files:

  + cktsim

    This directory holds circuit simulation results which are used to calibrate
    voltage-frequency model. Currently, there are two kinds of circuits
    available: an inverter, and ripple-carry adder with various bit widths.
    Technology nodes are 45nm down through 16nm with PTM. And two technology
    variants are supported, a high-performance HKMGS and a low power LP variant.

  + kernels

    This directory holds pre-defined synthetic kernels in XML format.

  + workloads

    This directory holds pre-defined synthetic workloads in XML format.

* lumos

  This directory holds the main source files of the framework. More
  details in the doc.

* tools

  Misc. scripts
