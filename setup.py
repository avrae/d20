import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = [line.strip() for line in fh.readlines()]

setuptools.setup(
    name="d20",
    version="0.6.4",
    author="Andrew Zhu",
    author_email="andrew@zhu.codes",
    description="A formal grammar-based dice parser and roller for D&D and other dice systems.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/avrae/formaldice",
    packages=setuptools.find_packages(exclude=('tests',)),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=requirements,
    include_package_data=True,
)
