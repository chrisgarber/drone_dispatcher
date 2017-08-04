from setuptools import setup, find_packages
from os import path
from codecs import open
import re



currentDir = path.abspath(path.dirname(__file__))

with open(path.join(currentDir, 'README.rst'), encoding='utf-8') as readme_file:
    longDescription = readme_file.read()

def read(*names, **kwargs):
    with open(
        path.join(currentDir, *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")
    
setup(
	name='drone_dispatcher',
    description="A python script for dispatching drones",
    long_description = longDescription,
    version=find_version('drone_dispatcher/drone_dispatcher.py'),
    author="Chris Garber",
    author_email="christophermgarber@gmail.com",
    url = 'https://github.com/chrisgarber/drone_dispatcher',
    license='GNU GPLv3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU GPLv3',

        'Programming Language :: Python :: 3.6.2',
    ],

    python_requires='>=3',
    keywords = 'dispatching drones package destination location',
    packages=find_packages(exclude=['tests']),
    install_requires=['numpy', 'requests'],

	entry_points={
        'console_scripts': [
            'drone_dispatcher=drone_dispatcher.__main__:main',
        ],
    },


	)

