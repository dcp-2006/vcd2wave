from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="vcd2wave",
    version="1.0.0",
    author="d1985",
    description="VCD waveform to HTML visualizer - lightweight and dependency-free",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/d1985/vcd2wave",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Development Status :: 4 - Beta",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "vcd2wave=vcd2wave:main",
        ],
    },
)
