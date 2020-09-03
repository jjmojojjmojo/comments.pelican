from setuptools import setup, find_packages
setup(
    name = "comments.pelican",
    version = "0.1",
    packages = find_packages('src'),
    package_dir = {'':'src'},
    install_requires = [
        "pelican",
        "markdown",
        "hashids",
        "arrow"
    ],
)