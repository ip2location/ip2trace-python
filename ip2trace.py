from __future__ import print_function
import socket
import struct
import os
import time
import sys
import select
import argparse
import IP2Location
from re import match

ICMP_ECHO = 8
ICMP_V6_ECHO = 128
ICMP_ECHO_REPLY = 0
ICMP_V6_ECHO_REPLY = 129
ICMP_TIME_EXCEEDED = 11
MIN_SLEEP = 1000

ip2location_result_fields = ['country_short', 'country_long', 'region', 'city', 'isp', 'latitude', 'longitude', 'domain', 'zipcode', 'timezone', 'netspeed', 'idd_code', 'area_code', 'weather_code', 'weather_name', 'mcc', 'mnc', 'mobile_brand', 'elevation', 'usage_type', ]

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

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--ip', metavar='Specify an IP address or hostname.')
    parser.add_argument('-d', '--database', metavar='Specify the path of IP2Location BIN database file.')
    parser.add_argument('-t', '--ttl', default=30, type=int, metavar='Set the max number of hops. (Default: 30)')

    return parser

def print_usage():
    print(
"Usage:\n"
"  ip2trace.py -p [IP ADDRESS/HOSTNAME] -d [IP2LOCATION BIN DATA PATH] [OPTIONS]\n\n"
"  -d, --database\n"
"  Specify the path of IP2Location BIN database file.\n"
"\n"
"  -h, -?, --help\n"
"  Display this guide.\n"
"\n"
"  -p, --ip\n"
"  Specify an IP address or hostname.\n"
"\n"
"  -t, --ttl\n"
"  Set the max number of hops. (Default: 30)\n"
"\n"
"  -v, --version\n"
"  Print the version of the IP2Location version.\n")

def print_version():
    print(
"IP2Location Geolocation Traceroute (ip2trace) Version 2.1.1\n"
"Copyright (c) 2021 IP2Location.com [MIT License]\n"
"https://www.ip2location.com/free/traceroute-application\n")

def traceroute(destination_server, database, ttl):
    t = Traceroute(destination_server, database, ttl)
    t.start_traceroute()

class Traceroute:
    def __init__(self, destination_server, database, max_hops):
        self.destination_server = destination_server
        self.database = database
        self.max_hops = max_hops
        self.identifier = os.getpid() & 0xffff
        self.seq_no = 0
        self.delays = []
        self.prev_sender_hostname = ""

        self.count_of_packets = 1
        self.packet_size = 80
        self.timeout = 1000
        self.ttl = 1

        if (destination_server is None):
            print ("Missing IP address or hostname.")
            sys.exit()

        try:
            self.destination_ip = to_ip(destination_server)
        except socket.gaierror:
            self.print_unknownhost()
            sys.exit()

        # Open up IP2Location BIN file
        if (database is not None):
            if os.path.isfile(database) == False:
                print("BIN database file not found.")
                sys.exit()
            else:
                self.obj = IP2Location.IP2Location(database)
        else:
            print("You must used IP2Location BIN database along with this tool. You can download free database at https://lite.ip2location.com.")
            sys.exit()

    def print_start(self):
        print("IP2Location Geolocation Traceroute (ip2trace) Version 2.1.1\n"
"Copyright (c) 2021 IP2Location.com [MIT License]\n"
"https://www.ip2location.com/free/traceroute-application\n\n")

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

    def print_trace(self, delay, ip_header):
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
                    print(" {}  {}  {:.4f}ms ".format(self.ttl, ip, delay), end="")
                else:
                    print("{}  {}  {:.4f}ms ".format(self.ttl, ip, delay), end="")
            else:
                if self.ttl < 10:
                    print(" {}  {}  {:.4f}ms ".format(self.ttl, ip, delay), end="")
                else:
                    print("{}  {}  {:.4f}ms ".format(self.ttl, ip, delay), end="")
                display_result = '['
                record_dict = {}
                for attr, value in record.__dict__.items():
                    record_dict[attr] = value
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
            if MIN_SLEEP > delay:
                time.sleep((MIN_SLEEP - delay) / 1000)

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
                print("Socket Error: {}".format(err))
            sys.exit()
        self.seq_no += 1
        if self.ttl == 1 and self.seq_no == 1:
            self.print_start()
        sent_time = self.send_icmp_echo(icmp_socket)
        if sent_time is None:
            return
        receive_time, icmp_header, ip_header = self.receive_icmp_reply(icmp_socket)
        icmp_socket.close()
        if receive_time:
            delay = (receive_time - sent_time) * 1000.0
            self.print_trace(delay, ip_header)
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
            print("Socket Error: %s", err)
            icmp_socket.close()
            return
        return send_time

    def receive_icmp_reply(self, icmp_socket):
        timeout = self.timeout / 1000
        time_limit = timer() + timeout
        while True:
            inputReady, _, _ = select.select([icmp_socket], [], [], timeout)
            receive_time = timer()
            if receive_time > time_limit:  # timeout
                self.print_timeout()
                return None, None, None
            packet_data, address = icmp_socket.recvfrom(1024)
            icmp_keys = ['type', 'code', 'checksum', 'identifier', 'sequence number']
            icmp_header = self.header_to_dict(icmp_keys, packet_data[20:28], "!BBHHH")
            ip_keys = ['VersionIHL', 'Type_of_Service', 'Total_Length', 'Identification', 'Flags_FragOffset', 'TTL', 'Protocol', 'Header_Checksum', 'Source_IP', 'Destination_IP']
            ip_header = self.header_to_dict(ip_keys, packet_data[:20], "!BBHHHBBHII")
            return receive_time, icmp_header, ip_header

# if __name__ == '__main__':
def main():
    is_help = False
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
            destination_server = args.ip
            database = args.database
            max_hops = args.ttl
            traceroute(destination_server, database, max_hops)
    else:
        print("Missing parameters. Please refer to documentation for the available parameters.")
