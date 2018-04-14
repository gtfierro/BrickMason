from setuptools import setup, find_packages
print find_packages()
setup(name='mason',
      version='0.0.1',
      description='Brick generation',
      url='https://github.com/SoftwareDefinedBuildings/XBOS',
      author='Gabe Fierro',
      author_email='gtfierro@cs.berkeley.edu',
      packages=find_packages(),
      scripts=['bin/mason'],
      #include_package_data=True,
      install_requires=[
        'pytoml>=0.1.14',
        'xbos>=0.0.28',
        'rdflib',
      ],
      zip_safe=False)


