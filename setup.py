from setuptools import setup, find_packages

setup(
    name='multi',
    version='0.1.0',    
    description='multiprocessing python functions',
    url='https://github.com/LeSasse/multi',
    author='Leonard Sasse',
    author_email='l.sasse@fz-juelich.de',
    license='GPL v3.0',
    packages=find_packages(),
    install_requires=['pandas>=1.1.2',
                      'numpy>=1.19.1',
                      'nilearn>=0.8.1',
                      'datalad==0.14.8',
                      ],

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',  
        'Operating System :: POSIX :: Linux',        
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    python_requires='>=3.6',
    include_package_data=True,
    package_data={'':['masks/*']}
)

