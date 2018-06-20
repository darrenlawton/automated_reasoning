from setuptools import setup

setup(
    name='SAT-Based Prover ',
    version='1.0',
    packages=['prover', 'clausal'],
    package_dir={'src'},
    url='',
    author='Darren Lawton',
    author_email='darren.lawton@anu.edu.au',
    description='SAT-Based Theorem Prover for Modal Logic K',
    classifiers=[
        'Environment :: Console',
        'License :: OSI Approved :: MIT',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=['ply', 'z3-solver']  # external packages as dependencies
)

