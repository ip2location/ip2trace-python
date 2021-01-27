import setuptools

with open("readme.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name="IP2Trace",
	version="1.0.0",
	author="IP2Location",
	author_email="support@ip2location.com",
	description="A Python traceroute tools that displaying geolocation information using IP2Location database.",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/ip2location/ip2trace-python",
	license='MIT',
	keywords='IP2Location Geolocation',
	project_urls={
		'Official Website': 'https://www.ip2location.com',
	},
	packages=setuptools.find_packages(),
	classifiers=(
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Developers",
		"Topic :: Software Development :: Libraries :: Python Modules",
		"Programming Language :: Python :: 3.5",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	),
)