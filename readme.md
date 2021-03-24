# IP2Trace Python

IP2Trace Python is a Python tool allowing user to get IP address information such as country, region, city, latitude, longitude, zip code, time zone, ISP, domain name, connection type, area code, weather, mobile network, elevation, usage type from traceroute probes IP address.

*Note: This tool requires Python 2.7, or Python 3.5 or later.*

## Installation

You can install this tool by using pip. Just type `pip install IP2Trace` in your console and IP2Trace will be installed in your machine.

*Note: This tool require [IP2Location](https://github.com/chrislim2888/IP2Location-Python) library to work with. If pip did not install the dependency for you, you can manually install it by using `pip install IP2Location`.*

## Usage

```
ip2trace -p [IP ADDRESS/HOSTNAME] -d [IP2LOCATION BIN DATA PATH] [OPTIONS]

  -d, --database
  Specify the path of IP2Location BIN database file.

  -h, -?, --help
  Display this guide.

  -p, --ip
  Specify an IP address or hostname.

  -t, --ttl
  Set the maxinum TTL for each probe.

  -v, --version
  Print the version of the IP2Location version.
```

#### Example

Traceroute an IP address.

```bash
ip2trace -p 8.8.8.8 -d /usr/share/ip2location/DB3.BIN
```

Example output:

```bash
IP2Location Geolocation Traceroute (ip2trace) Version 8.0.0
Copyright (c) 2021 IP2Location.com [MIT License]
https://www.ip2location.com/free/traceroute-application


 1  37.123.114.1  0.3853ms ["GB","United Kingdom of Great Britain and Northern Ireland","England","London"]
 2  10.10.32.132  0.4084ms ["-","-","-","-"]
 3  10.10.32.17  0.2673ms ["-","-","-","-"]
 4  212.78.92.2  0.5546ms ["GB","United Kingdom of Great Britain and Northern Ireland","England","London"]
 5  98.158.181.98  1.8706ms ["US","United States of America","New York","New York City"]
 6  195.66.236.125  0.5715ms ["GB","United Kingdom of Great Britain and Northern Ireland","England","London"]
 7  108.170.246.129  0.5193ms ["US","United States of America","California","Mountain View"]
 8  108.170.232.97  0.4749ms ["US","United States of America","California","Mountain View"]
 9  8.8.8.8  0.5693ms ["US","United States of America","California","Mountain View"]
```

Traceroute by hostname

```bash
ip2trace -p google.com -d /usr/share/ip2location/DB3.BIN
```

Example output:

```bash
IP2Location Geolocation Traceroute (ip2trace) Version 8.0.0
Copyright (c) 2021 IP2Location.com [MIT License]
https://www.ip2location.com/free/traceroute-application


 1  37.123.114.1  0.3529ms ["GB","United Kingdom of Great Britain and Northern Ireland","England","London"]
 2  10.10.32.131  0.3686ms ["-","-","-","-"]
 3  10.10.32.17  0.2663ms ["-","-","-","-"]
 4  212.78.92.2  19.7358ms ["GB","United Kingdom of Great Britain and Northern Ireland","England","London"]
 5  98.158.181.98  9.2373ms ["US","United States of America","New York","New York City"]
 6  195.66.236.125  0.5388ms ["GB","United Kingdom of Great Britain and Northern Ireland","England","London"]
 7  108.170.246.161  1.6131ms ["US","United States of America","California","Mountain View"]
 8  172.253.65.211  1.2376ms ["US","United States of America","California","Mountain View"]
 9  216.58.213.14  0.5167ms ["US","United States of America","California","Mountain View"]
```



## Download IP2Location Databases

- Download free IP2Location LITE databases at [https://lite.ip2location.com](https://lite.ip2location.com/)
- For more accurate commercial database, please refer to [https://www.ip2location.com](https://www.ip2location.com/)

One you have obtained your download token, you can download the the database using **wget** as below:

```
wget "https://www.ip2location.com/download?token={DOWNLOAD_TOKEN}&file={DATABASE_CODE}"
```

## Support

Email: [support@ip2location.com](mailto:support@ip2location.com)
URL: [https://www.ip2location.com](https://www.ip2location.com/)