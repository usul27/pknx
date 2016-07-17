from setuptools import setup, find_packages

setup(name='knxip',
      version='0.3.1',
      description='A native Python KNX/IPNet implementation',
      url='http://github.com/usul27/pknx',
      author='Daniel Matuschek',
      author_email='daniel@matuschek.net',
      license='MIT',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'Topic :: System :: Hardware :: Hardware Drivers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5'
      ],
      packages=find_packages(),
      keywords='knx ip automation',
      zip_safe=False)
