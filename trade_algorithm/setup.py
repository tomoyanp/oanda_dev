from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext



ext_modules = [Extension('expantion_algo_cython', ['expantion_algo_cython.pyx'])]   #assign new.pyx module in setup.py.
setup(

      name        = 'expantion_algo_cython app',

      cmdclass    = {'build_ext':build_ext},

      ext_modules = ext_modules

      )
