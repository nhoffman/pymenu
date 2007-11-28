"""
Create unix package: python setup.py sdist
Create windows package: python setup.py bdist_wininst
"""

revision = '$Revision: 1488 $'

from distutils.core import setup
setup(name='Menu',
      version=revision[:-1].split(':')[1].strip(),
      py_modules=['Menu'],
      description='Creates a simple, interactive text-based user interface',
      author='Noah Hoffman',
      author_email='noah.hoffman@gmail.com',
      url='http://staff.washington.edu/ngh2',
      )
