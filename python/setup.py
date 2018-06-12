from setuptools import setup, find_packages
print find_packages()
setup(name='brickmason',
      version='0.0.2',
      description='Brick generation',
      url='https://github.com/SoftwareDefinedBuildings/XBOS',
      author='Gabe Fierro',
      author_email='gtfierro@cs.berkeley.edu',
      packages=find_packages(),
      scripts=['bin/brickmason'],
      #include_package_data=True,
      install_requires=[
        'pytoml>=0.1.14',
        'xbos>=0.0.28',
        'rdflib',
        'coloredlogs'
      ],
      zip_safe=False)


