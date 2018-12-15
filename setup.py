from setuptools import setup

setup(name='peex',
      version='1.0',
      description='PEEX is a non-interactive FTP client for updating webpages',
      author='Magnus Olsson',
      author_email='magnus@minimum.se',
      url='https://github.com/blastur/PEEX',
      packages=['peex'],
      scripts=['bin/peex'],
     )