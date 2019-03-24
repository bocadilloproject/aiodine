"""Package setup."""

import setuptools

description = "Async-first dependency injection library for Python"

with open("README.md", "r") as readme:
    long_description = readme.read()

GITHUB = "https://github.com/bocadilloproject/aiodine"

setuptools.setup(
    name="aiodine",
    version="1.2.2",
    author="Florimond Manca",
    author_email="florimond.manca@gmail.com",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=[
        "async_exit_stack;python_version<'3.7'",
        "aiocontextvars;python_version<'3.7'",
    ],
    python_requires=">=3.6",
    url=GITHUB,
    license="MIT",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Framework :: AsyncIO",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
