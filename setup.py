import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = 'namemaker',
    version = '1.1.1',
    author = 'Rick Moyer',
    author_email = 'rickmoyer.sd@gmail.com',
    description = 'A random name generator using Markov chains.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/Rickmsd/namemaker',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Topic :: Games/Entertainment'
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    package_data = {'namemaker': ['name data/*.txt']}
)
