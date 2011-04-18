"""
Create unix package: python setup.py sdist
Create windows package: python setup.py bdist_wininst
"""

from Menu import __version__

from distutils.core import setup
setup(name = 'Menu',
      version = __version__,
      py_modules = ['Menu'],
      description = 'Creates a simple, interactive text-based user interface',
      author = 'Noah Hoffman',
      author_email = 'noah.hoffman@gmail.com',
      url = 'https://github.com/nhoffman/pymenu',
      )
