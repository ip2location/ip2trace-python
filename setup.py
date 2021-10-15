import setuptools
import platform, os

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="IP2Trace",
    version="2.1.7",
    description="A Python tool to display geolocation information in the traceroute.",
    long_description_content_type="text/markdown",
    long_description=long_description,
    entry_points={
        'console_scripts': [
            'ip2trace=ip2trace:main'
        ]
    },
    py_modules=['ip2trace'],
    author="IP2Location",
    author_email="support@ip2location.com",
    url="https://github.com/ip2location/ip2trace-python",
    license='MIT',
    keywords='IP2Location Geolocation',
    project_urls={
        'Official Website': 'https://www.ip2location.com',
    },
    install_requires=['IP2Location'],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    packages=setuptools.find_packages() + ['.'],
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Environment :: Console",
        "Topic :: Utilities",
        'Programming Language :: Python :: 2.7',
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)