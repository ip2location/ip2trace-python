# IP2Trace Python

IP2Trace Python is a Python tool allowing user to get IP address information such as country, region, city, latitude, longitude, zip code, time zone, ISP, domain name, connection type, area code, weather, mobile network, elevation, usage type from traceroute probes IP address.

*Note: This tool requires Python 3.5 or later.*

## Usage

```
python ip2trace.py -p [IP ADDRESS/HOSTNAME] -d [IP2LOCATION BIN DATA PATH] [OPTIONS]

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
python ip2trace.py -p 8.8.8.8 -d /usr/share/ip2location/DB3.BIN
```

Traceroute by hostname

```bash
python ip2trace.py -p google.com -d /usr/share/ip2location/DB3.BIN
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