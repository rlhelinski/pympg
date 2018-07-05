#!/usr/bin/env python

from distutils.core import setup

setup(name='pympg',
      version='3.0-dev',
      description='Simple Python tool for tracking gas mileage '
                  'with a GTK graphical interface',
      author='Ryan Helinski',
      author_email='rlhelinski@gmail.com',
      url='https://www.github.com/rlhelinski/pympg',
      packages=['pympg'],
      package_data={'pympg': ['icons/*.png', 'icons/*.svg']},
      scripts=['PyMPG.py'],
      install_requires=[
          'pygobject==3.28.3',
          ],
      )
