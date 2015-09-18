#!/usr/bin/env python
import logging
import numpy
import scipy

def random_uc_cov(dist, param1, param2):
    """randomly generate kernel coverage that follows the specified distribution

    Parameters
    ----------
    dist : str
      the name of the distribution, currently, only support the following three

      - 'norm': normal distribution (Gaussian)
      - 'lognorm': log-normal distribution
      - 'uniform': uniform distribution

    param1, param2 : float
      The statistical parameters for the distribution. When dist is 'norm' or
      'lognorm', param1 represents the mean, param2 represents the standard
      deviation (std). When dist is 'uniform', param1, param2 represent the lower
      and upper bound of the distribution

    Returns
    -------
    float
      the generated random coverage. 0 will be return instead if there are any
      errors

    """
    _logger = logging.getLogger(__name__)
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
        _logger.error('Unknown distribution for coverage: %s', dist)
        r = 0

    return r


def random_kernel_cov(cov_params):
    _logger = logging.getLog(__name__)
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
        _logger.error('Unknown distribution for coverage: %s', dist)
        r = 0

    return r


# class AppMMM(dict):
#         self["GPU"] = KernelParam(perf=3.41,power=0.74, bw=0.725)
#         self["FPGA"] = KernelParam(perf=0.75,power=0.31, bw=0.325)
#         self["ASIC"] = KernelParam(perf=27.4,power=0.79, bw=3.62)
#         self["O3CPU"] = KernelParam(perf=1,power=1, bw=0.216)
#         self["IO"] = KernelParam(perf=1,power=1, bw=0.16)

# class AppBS(dict):
#         self["GPU"] = KernelParam(perf=17.0,power=0.57, bw=5.85)
#         self["FPGA"] = KernelParam(perf=5.68,power=0.26, bw=3.975)
#         self["ASIC"] = KernelParam(perf=482,power=4.75, bw=66.249)
#         self["O3CPU"] = KernelParam(perf=1,power=1, bw=0.35)
#         self["IO"] = KernelParam(perf=1,power=1, bw=0.26)

# class AppFFT64(dict):
#         self["GPU"] = KernelParam(perf=2.42,power=0.59, bw = 1)
#         self["FPGA"] = KernelParam(perf=2.81,power=0.29, bw = 1)
#         self["ASIC"] = KernelParam(perf=733,power=5.34, bw = 1)
#         self["O3CPU"] = KernelParam(perf=1,power=1, bw=1)
#         self["IO"] = KernelParam(perf=1,power=1, bw=1)
