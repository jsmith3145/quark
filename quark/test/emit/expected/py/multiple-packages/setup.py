# Setup file for package multiple_packages

from setuptools import setup

setup(name="multiple_packages",
      version="0.0.1",
      install_requires=["datawire-quark-core==0.3.1"],
      packages=['reflect', 'p1', 'p1.p2', 'multiple_packages_md'])