Description
===========

Heterogeneous multi-core system, where several big cores for latency-sensitive
serial part, and some massive little cores and/or TFET cores for throughput, as
in parallel part. The system ONLY contains a single ASIC to accelerate kernel.
Accordingly, the studied application (in workload.xml) has only one kernel.



System organizations:
* One Big O3 core with CMOS
* Several small IO cores with either CMOS or TFET
* The rest of area allocated to a single ASIC
* Several alternative system budget (large, power_constrained, etc.)

Applications:
* 100% parallel, or 90% parallel
* kernel coverage: 10%, 20%, 30%, 40%, 50%
* asic allocation: 5%, 10%, 15%, 20%, 25%
* asic speedup: 5x, 10x, 50x
