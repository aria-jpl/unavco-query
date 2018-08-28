from setuptools import setup, find_packages
import unavco

setup(
    name='unavco',
    version=unavco.__version__,
    long_description=unavco.__description__,
    url=unavco.__url__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'qquery>=0.0.1'
    ]
)
