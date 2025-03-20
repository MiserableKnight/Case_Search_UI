from setuptools import find_packages, setup

setup(
    name="text-anonymizer",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "spacy>=3.0.0",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for anonymizing sensitive information in text",
    url="https://github.com/yourusername/text-anonymizer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
