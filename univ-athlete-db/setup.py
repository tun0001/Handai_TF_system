from setuptools import setup, find_packages

setup(
    name='univ-athlete-db',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A system to scrape athletic results and manage university athlete records in a database.',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'requests',
        'beautifulsoup4',
        'sqlalchemy',
        'pytest',
    ],
    entry_points={
        'console_scripts': [
            'univ-athlete-db=cli:main',
        ],
    },
)