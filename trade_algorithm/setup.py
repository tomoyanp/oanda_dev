from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize

extentions = [Extension("*", ["*.pyx"])]

setup(

      name        = 'trade_wrapper',

      cmdclass    = {'build_ext':build_ext},

      ext_modules = cythonize(extentions)

      )
