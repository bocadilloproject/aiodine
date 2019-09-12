"""Package setup."""

import setuptools

description = "Async-first dependency injection library for Python"

with open("README.md", "r") as readme:
    long_description = readme.read()

GITHUB = "https://github.com/bocadilloproject/aiodine"

setuptools.setup(
    name="aiodine",
    version="1.2.8",
    author="Florimond Manca",
    author_email="florimond.manca@gmail.com",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    package_data={"aiodine": ["py.typed"]},
    python_requires=">=3.6",
    install_requires=[
        "async_generator; python_version<'3.7'",
        "async_exit_stack; python_version<'3.7'",
    ],
    url=GITHUB,
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
