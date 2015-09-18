from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

setup(
    name = "lumos",
    ext_modules = cythonize([
        "lumos/model/acc.pyx",
        "lumos/model/core/base.pyx",
        "lumos/model/system/hetero.pyx",
        "lumos/model/workload/kernel.pyx"
    ]),
)
