from __future__ import print_function
import socket
import struct
import os
import platform
import time
import sys
import select
import argparse
import IP2Location
from re import match
from shutil import copyfile

ICMP_ECHO = 8
ICMP_V6_ECHO = 128
ICMP_ECHO_REPLY = 0
ICMP_V6_ECHO_REPLY = 129
ICMP_TIME_EXCEEDED = 11
MIN_SLEEP = 1000

# Windows IPv6 compatibility
# if PLATFORM_WINDOWS:
if platform.system() == 'Windows':
    socket.IPPROTO_IPV6 = 41
    socket.IPPROTO_ICMPV6 = 58

ip2location_result_fields = ['country_short', 'country_long', 'region', 'city', 'isp', 'latitude', 'longitude', 'domain', 'zipcode', 'timezone', 'netspeed', 'idd_code', 'area_code', 'weather_code', 'weather_name', 'mcc', 'mnc', 'mobile_brand', 'elevation', 'usage_type', 'address_type', 'category', ]
ip2location_outputs_reference = ['country_code', 'country_name', 'region_name', 'city_name', 'isp', 'latitude', 'longitude', 'domain', 'zip_code', 'time_zone', 'net_speed', 'idd_code', 'area_code', 'weather_station_code', 'weather_station_name', 'mcc', 'mnc', 'mobile_brand', 'elevation', 'usage_type', 'address_type', 'category', ]

# Define BIN database default path
if platform.system() == 'Windows':
    default_path = os.path.expanduser('~') + os.sep + "Documents" + os.sep
# elif platform.system() === 'Linux ':
else:
    default_path = '/usr/share/ip2location/'

# Now we copy the BIN database to default_path here instead of doing it duing installation as pip kept copied to wrong location.
if (os.path.isfile(default_path + "IP2LOCATION-LITE-DB1.IPV6.BIN") == False):
    try:
        # create the dir is not exist
        if (os.path.exists(default_path) is False):
            os.mkdir(default_path)
        copyfile(os.path.dirname(os.path.realpath(__file__)) + os.sep + "data" + os.sep + "IP2LOCATION-LITE-DB1.IPV6.BIN", default_path + "IP2LOCATION-LITE-DB1.IPV6.BIN")
    except PermissionError as e:
        sys.exit("Root permission is required. Please rerun it as 'sudo ip2trace'.")

if sys.platform.startswith('win32'):
    timer = time.clock
else:
    timer = time.time

def calculate_checksum(packet):
    countTo = (len(packet) // 2) * 2
    count = 0
    sum = 0
    while count < countTo:
        if sys.byteorder == "little":
            loByte = packet[count]
            hiByte = packet[count + 1]
        else:
            loByte = packet[count + 1]
            hiByte = packet[count]
        sum = sum + (hiByte * 256 + loByte)
        count += 2
    if countTo < len(packet):
        sum += packet[count]
    sum = (sum >> 16) + (sum & 0xffff)
    sum += (sum >> 16)
    answer = ~sum & 0xffff
    answer = socket.htons(answer)
    return answer

def is_ipv4(hostname):
    pattern = r'^([0-9]{1,3}[.]){3}[0-9]{1,3}$'
    if match(pattern, hostname) is not None:
        return 4
    return False

def is_ipv6(hostname):
    if ':' in hostname:
        return 6
    return False

def is_valid_ip(hostname):
    if is_ipv4(hostname) is not False or is_ipv6(hostname) is not False:
        return True
    else:
        return False

def to_ip(hostname):
    if is_valid_ip(hostname):
        return hostname
    return socket.gethostbyname(hostname)

def ip_to_domain_name(hostname):
    if is_valid_ip(hostname):
        return socket.gethostbyaddr(hostname)
    return hostname


def create_parser():
    parser = argparse.ArgumentParser()
    # parser.add_argument('-p', '--ip', metavar='Specify an IP address or hostname.')
    gp = parser.add_mutually_exclusive_group()
    gp.add_argument('-p', '--ip', metavar='Specify an IP address or hostname.')
    gp.add_argument('hostname', nargs='?', metavar='Specify an IP address or hostname.')
    parser.add_argument('-d', '--database', metavar='Specify the path of IP2Location BIN database file.')
    parser.add_argument('-t', '--ttl', default=30, type=int, metavar='Set the max number of hops. (Default: 30)')
    parser.add_argument('-o', '--output', metavar='Specify the result columns to be output.', nargs='+')
    parser.add_argument('-a', '--all', action='store_true')

    return parser

def print_usage():
    print(
"Usage: ip2trace -p [IP ADDRESS/HOSTNAME] -d [IP2LOCATION BIN DATA PATH] [OPTIONS]\n"
"   or: ip2trace [IP ADDRESS/HOSTNAME] -d [IP2LOCATION BIN DATA PATH] [OPTIONS]\n\n"
"  -p, --ip\n"
"  Specify an IP address or hostname.\n"
"  The -p/--ip can be omitted if the IP address or hostname is defined in the first parameter.\n"
"\n"
"  -d, --database\n"
"  Specify the path of IP2Location BIN database file. You can download the latest free IP2Location BIN database from https://lite.ip2location.com.\n"
"\n"
"  -t, --ttl\n"
"  Set the max number of hops. (Default: 30)\n"
"\n"
"  -o, --output\n"
"  Set the desired IP2Location BIN database columns to output with.\n"
"  Available columns are: country_code, country_name, region_name, city_name, isp, latitude, longitude, domain, zip_code, time_zone, net_speed, idd_code, area_code, weather_station_code, weather_station_name, mcc, mnc, mobile_brand, elevation, usage_type.\n"
"\n"
"  -a, --all\n"
"Print all the column(s) available based on the BIN file used.\n"
"\n"
"  -h, -?, --help\n"
"  Display this guide.\n"
"\n"
"  -v, --version\n"
"  Print the version of the IP2Location version.\n")

def print_version():
    print(
"IP2Location Geolocation Traceroute (ip2trace) Version 2.1.7\n"
"Copyright (c) 2021 IP2Location.com [MIT License]\n"
"https://www.ip2location.com/free/traceroute-application\n")

def traceroute(destination_server, database, ttl, output, all):
    t = Traceroute(destination_server, database, ttl, output, all)
    t.start_traceroute()

class Traceroute:
    def __init__(self, destination_server, database, max_hops, output, all):
        self.destination_server = destination_server
        self.database = database
        self.max_hops = max_hops
        self.output = output
        self.identifier = os.getpid() & 0xffff
        self.seq_no = 0
        self.delays = []
        self.prev_sender_hostname = ""
        self.all = all

        self.count_of_packets = 1
        self.packet_size = 80
        self.timeout = 1000
        self.ttl = 1

        if (destination_server is None):
            print ("Missing IP address or hostname.")
            sys.exit()

        try:
            self.destination_ip = to_ip(destination_server)
            self.destination_domain_name = ip_to_domain_name(destination_server)
        except socket.gaierror:
            self.print_unknownhost()
            sys.exit()

        # Open up IP2Location BIN file
        if (database is not None):
            if os.path.isfile(database) == False:
                # Now will check if the filename passed is a BIN extension or not
                if database.upper().endswith(".BIN"):
                    # check if the given filename is under current dir or not.
                    if (os.getcwd().endswith(os.sep)):
                        filepath = os.getcwd() + database
                    else:
                        filepath = os.getcwd() + os.sep + database
                    # print(filepath)
                    if os.path.isfile(filepath) == False:
                        if os.path.isfile(default_path + database) == False:
                            print("BIN database file not found.")
                            sys.exit()
                        else:
                            self.obj = IP2Location.IP2Location(default_path + database)
                    else:
                        self.obj = IP2Location.IP2Location(filepath)
                else:
                    print("Only BIN database is accepted. You can download the latest free IP2Location BIN database from https://lite.ip2location.com.")
                    sys.exit()
            else:
                self.obj = IP2Location.IP2Location(database)
        else:
            if (os.path.isfile(default_path + "IP2LOCATION-LITE-DB1.IPV6.BIN") != False):
                self.obj = IP2Location.IP2Location(default_path + "IP2LOCATION-LITE-DB1.IPV6.BIN")
            else:
                print("Missing IP2Location BIN database. Please enter ‘ip2trace -h’ for more information.")
                sys.exit()

        # check the output list
        if (self.output is not None):
            for i in self.output:
                if i not in ip2location_outputs_reference:
                    print("The column name is invalid. Please get a list of valid column names at https://ip2location.com/database/db24-ip-country-region-city-latitude-longitude-zipcode-timezone-isp-domain-netspeed-areacode-weather-mobile-elevation-usagetype.")
                    sys.exit()

    def print_start(self):
        print("IP2Location Geolocation Traceroute (ip2trace) Version 2.1.7\n"
"Copyright (c) 2021 IP2Location.com [MIT License]\n"
"https://www.ip2location.com/free/traceroute-application\n\n")
# "Traceroute to", self.destination_domain_name, "(", self.destination_ip, ")\n\n")
# "Traceroute to", self.destination_domain_name[0], "(", self.destination_ip, ")\n\n")
        print("Traceroute to", self.destination_domain_name[0], "(", self.destination_ip, ")\n\n", end="")

    def print_unknownhost(self):
        print("traceroute: unknown host {}".format(self.destination_server))

    def print_timeout(self):
        if self.seq_no == 1:
            if self.ttl < 10:
                print(" {}  ".format(self.ttl), end="")
            else:
                print("{}  ".format(self.ttl), end="")
        print("* ", end="")
        if self.seq_no == self.count_of_packets:
            print()

    # def print_trace(self, delay, ip_header):
    def print_trace(self, delays, ip_header):
        total_delays = 0
        ip = socket.inet_ntoa(struct.pack('!I', ip_header['Source_IP']))
        try:
            sender_hostname = socket.gethostbyaddr(ip)[0]
        except socket.herror:
            sender_hostname = ip
        if self.prev_sender_hostname != sender_hostname:
            record = None
            if is_valid_ip(ip):
                record = self.obj.get_all(ip)
            if record is None:
                if self.ttl < 10:
                    # print(" {}  {}  {:.3f}ms ".format(self.ttl, ip, delay), end="")
                    print(" {}  {}  ".format(self.ttl, ip), end="")
                    for i in range(0, len(delays)):
                        total_delays = total_delays + delays[i]
                        print("{:.3f}ms ".format(delays[i]), end="")
                else:
                    # print("{}  {}  {:.3f}ms ".format(self.ttl, ip, delay), end="")
                    # print("{}  {}  {:.3f}ms ".format(self.ttl, ip, delay), end="")
                    print("{}  {}  ".format(self.ttl, ip), end="")
                    for i in range(0, len(delays)):
                        total_delays = total_delays + delays[i]
                        print("{:.3f}ms ".format(delays[i]), end="")
            else:
                if self.ttl < 10:
                    # print(" {}  {}  {:.3f}ms ".format(self.ttl, ip, delay), end="")
                    # print(" {}  {}  {:.3f}ms ".format(self.ttl, ip, delay), end="")
                    print(" {}  {}  ".format(self.ttl, ip), end="")
                    for i in range(0, len(delays)):
                        total_delays = total_delays + delays[i]
                        print("{:.3f}ms ".format(delays[i]), end="")
                else:
                    # print("{}  {}  {:.3f}ms ".format(self.ttl, ip, delay), end="")
                    # print("{}  {}  {:.3f}ms ".format(self.ttl, ip, delay), end="")
                    print("{}  {}  ".format(self.ttl, ip), end="")
                    for i in range(0, len(delays)):
                        total_delays = total_delays + delays[i]
                        print("{:.3f}ms ".format(delays[i]), end="")
                display_result = '['
                record_dict = {}
                for attr, value in record.__dict__.items():
                    record_dict[attr] = value
                # print(record_dict["region"])
                if (self.output is True):
                    for i in self.output:
                        if (i in ip2location_outputs_reference) and (ip2location_result_fields[ip2location_outputs_reference.index(i)] in record_dict) and (record_dict[ip2location_result_fields[ip2location_outputs_reference.index(i)]] is not None):
                            display_result = display_result + '"' + str(record_dict[ip2location_result_fields[ip2location_outputs_reference.index(i)]]) + '",'
                else:
                    # for i in range(0,len(ip2location_result_fields)):
                        # if (ip2location_result_fields[i] in record_dict) and (record_dict[ip2location_result_fields[i]] is not None):
                            # display_result = display_result + '"' + str(record_dict[ip2location_result_fields[i]]) + '",'
                    if (self.all is False) :
                        if "region" in record_dict:
                            display_result = display_result + '"' + str(record_dict["country_short"]) + '","' + str(record_dict["region"]) + '","' + str(record_dict["city"]) + '"'
                        else:
                            display_result = display_result + '"' + str(record_dict["country_short"]) + '"'
                    else :
                        for i in range(0,len(ip2location_result_fields)):
                            if (ip2location_result_fields[i] in record_dict) and (record_dict[ip2location_result_fields[i]] is not None):
                                display_result = display_result + '"' + str(record_dict[ip2location_result_fields[i]]) + '",'
                if display_result.endswith(','):
                    display_result = display_result[:-1]
                display_result = display_result + ']'
                print("{}".format(display_result), end="")
            self.prev_sender_hostname = sender_hostname
        else:
            print("{:.3f} ms ".format(delay), end="")
        if self.seq_no == self.count_of_packets:
            print()
            self.prev_sender_hostname = ""
            average_delays = total_delays / len(delays)
            # if MIN_SLEEP > delay:
                # time.sleep((MIN_SLEEP - delay) / 1000)
            if MIN_SLEEP > average_delays:
                time.sleep((MIN_SLEEP - average_delays) / 1000)

    def header_to_dict(self, keys, packet, struct_format):
        values = struct.unpack(struct_format, packet)
        return dict(zip(keys, values))

    def start_traceroute(self):
        icmp_header = None
        while self.ttl <= self.max_hops:
            self.seq_no = 0
            try:
                for i in range(self.count_of_packets):
                    icmp_header = self.tracer()
            except KeyboardInterrupt:  # handles Ctrl+C
                break
            self.ttl += 1
            if icmp_header is not None:
                if is_ipv4(self.destination_ip) == 4 and icmp_header['type'] == ICMP_ECHO_REPLY:
                    break
                elif is_ipv6(self.destination_ip) == 6 and icmp_header['type'] == ICMP_V6_ECHO_REPLY:
                    break

    def tracer(self):
        # try:
            # if is_ipv4(self.destination_ip) == 4:
                # icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                # icmp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, self.ttl)
            # elif is_ipv6(self.destination_ip) == 6:
                # icmp_socket = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6)
                # icmp_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_UNICAST_HOPS, self.ttl)
        # except socket.error as err:
            # if err.errno == 1:
                # print("Operation not permitted: ICMP messages can only be sent from a process running as root")
            # else:
                # print("Socket Error1: {}".format(err))
            # sys.exit()
        self.seq_no += 1
        if self.ttl == 1 and self.seq_no == 1:
            self.print_start()
        # sent_time = self.send_icmp_echo(icmp_socket)
        # if sent_time is None:
            # return
        # receive_time, icmp_header, ip_header = self.receive_icmp_reply(icmp_socket)
        # icmp_socket.close()
        # if receive_time:
            # delay = (receive_time - sent_time) * 1000.0
            # self.print_trace(delay, ip_header)
        delays = []
        # print(icmp_socket)
        for i in range (0, 3):
            try:
                if is_ipv4(self.destination_ip) == 4:
                    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                    icmp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, self.ttl)
                elif is_ipv6(self.destination_ip) == 6:
                    icmp_socket = socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6)
                    icmp_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_UNICAST_HOPS, self.ttl)
            except socket.error as err:
                if err.errno == 1:
                    print("Operation not permitted: ICMP messages can only be sent from a process running as root")
                else:
                    print("Socket Error1: {}".format(err))
                sys.exit()
            sent_time = self.send_icmp_echo(icmp_socket)
            if sent_time is None:
                return
            receive_time, icmp_header, ip_header = self.receive_icmp_reply(icmp_socket)
            # print ("Source_IP", ip_header['Source_IP'])
            icmp_socket.close()
            if receive_time:
                delay = (receive_time - sent_time) * 1000.0
                # print(delay)
                delays.append(delay)
            # time.sleep(0.1)
            # time.sleep(0.01)
            time.sleep(0.005)
        # if len(delays) > 0:
        if len(delays) > 0 and ip_header is not None:
            self.print_trace(delays, ip_header)
        else:
            self.print_timeout()
        return icmp_header

    def random_byte_message(self, size):
        '''
        Generate a random byte sequence of the specified size.
        '''
        sequence = choices(
            b'abcdefghijklmnopqrstuvwxyz'
            b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            b'1234567890', k=size)
        return bytearray(sequence)

    def send_icmp_echo(self, icmp_socket):
        if is_ipv4(self.destination_ip) == 4:
            header = struct.pack("!BBHHH", ICMP_ECHO, 0, 0, self.identifier, self.seq_no)
        elif is_ipv6(self.destination_ip) == 6:
            header = struct.pack("!BBHHH", ICMP_V6_ECHO, 0, 0, self.identifier, self.seq_no)
        start_value = 65
        payload = []
        for i in range(start_value, start_value+self.packet_size):
            payload.append(i & 0xff)
        data = bytearray(payload)
        checksum = calculate_checksum(header + data)
        if is_ipv4(self.destination_ip) == 4:
            header = struct.pack("!BBHHH", ICMP_ECHO, 0, checksum, self.identifier, self.seq_no)
        elif is_ipv6(self.destination_ip) == 6:
            header = struct.pack("!BBHHH", ICMP_V6_ECHO, 0, checksum, self.identifier, self.seq_no)
        packet = header + data
        send_time = timer()
        try:
            icmp_socket.sendto(packet, (self.destination_ip, 0))
        except socket.error as err:
            print("Socket Error2: %s", err)
            icmp_socket.close()
            return
        return send_time

    def receive_icmp_reply(self, icmp_socket):
        timeout = self.timeout / 1000
        time_limit = timer() + timeout
        # print ("timeout", timeout)
        # print ("time_limit", time_limit)
        while True:
            inputReady, _, _ = select.select([icmp_socket], [], [], timeout)
            receive_time = timer()
            # print ("receive_time", receive_time)
            if receive_time > time_limit:  # timeout
                # self.print_timeout()
                return None, None, None
            packet_data, address = icmp_socket.recvfrom(1024)
            icmp_keys = ['type', 'code', 'checksum', 'identifier', 'sequence number']
            icmp_header = self.header_to_dict(icmp_keys, packet_data[20:28], "!BBHHH")
            ip_keys = ['VersionIHL', 'Type_of_Service', 'Total_Length', 'Identification', 'Flags_FragOffset', 'TTL', 'Protocol', 'Header_Checksum', 'Source_IP', 'Destination_IP']
            ip_header = self.header_to_dict(ip_keys, packet_data[:20], "!BBHHHBBHII")
            # print ("Source_IP1", ip_header['Source_IP'])
            return receive_time, icmp_header, ip_header

# if __name__ == '__main__':
def main():
    is_help = False
    # print(sys.argv)
    if len(sys.argv) >= 2:
        for index, arg in enumerate(sys.argv):
            if arg in ['--help', '-h', '-?']:
                print_usage()
                is_help = True
            elif arg in ['--version', '-v']:
                print_version()
                is_help = True
        if is_help is False:
            parser = create_parser()
            args = parser.parse_args(sys.argv[1:])
            # destination_server = args.ip
            if args.ip is not None:
                destination_server = args.ip
            else:
                destination_server = args.hostname
            if args.all is not None:
                all = args.all
            else:
                all = False
            database = args.database
            max_hops = args.ttl
            output = args.output
            # print(all)
            # sys.exit()
            traceroute(destination_server, database, max_hops, output, all)
    else:
        print("Missing parameters. Please enter 'ip2trace -h' for more information.")
