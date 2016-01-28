# Setup file for package string_methods

from setuptools import setup

setup(name="string_methods",
      version="0.0.1",
      install_requires=["datawire-quark-core==0.4.2", "builtin==0.0.1"],
      py_modules=['string_methods'],
      packages=['string_methods_md'])
