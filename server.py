#!/usr/bin/python3
"""
WSJT-X to Cloudlog.

"""

import socket
import sys
# import time
import configparser
import asyncio
import requests


def qso(cloudlog_uri, data):
    response = requests.post(cloudlog_uri + '/index.php/api/qso', json=data)
    if response.status_code != 200:
        print("Status code: ", response.status_code)
        print(response.text)


class WsjtxToCloudlog:
    """ Class WsjtxToCloudlog """
    # pylint: disable=too-many-instance-attributes
    # These are all required variables.
    config = ""
    operator = ""
    county = ""
    call = ""
    date = ""
    time_on = ""
    time_off = ""
    band = ""
    mode = ""
    frequency = 0
    power = 0
    rst_sent = 0
    rst_rcvd = 0
    gridsquare = ""
    my_gridsquare = ""
    comments = ""
    recv_buffer = ""

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config')
        self.computer_name = socket.gethostname()
        self.cloudlog_uri = self.config['DEFAULT']['cloudlog_uri']
        self.cloudlog_key = self.config['DEFAULT']['cloudlog_key']
        self.cloudlog_station_id = self.config['DEFAULT']['cloudlog_station_id']
        self.reset_vals()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def reset_vals(self):
        """ Reset all values to beginning state """
        self.call = ""
        self.state = ""
        self.county = ""
        self.date = ""
        self.time_on = ""
        self.time_off = ""
        self.band = ""
        self.mode = ""
        self.freq = ""
        self.power = 0
        self.rst_sent = ""
        self.rst_rcvd = ""
        self.gridsquare = ""
        self.my_gridsquare = ""
        self.comment = ""
        self.lat = ""
        self.lon = ""
        self.country = ""
        self.dxcc = ""
        self.cqz = ""
        self.ituz = ""

    def parse_adif(self):
        """ Parse ADIF record """
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # It's a parser after all
        print("\nParsing log entry from WSJT-X...\n")
        for token in [
                'call', 'my_gridsquare', 'gridsquare', 'mode', 'rst_sent', 'rst_rcvd',
                'qso_date', 'time_on', 'qso_date_off', 'time_off', 'band',
                'freq', 'station_callsign', 'my_gridsquare', 'tx_pwr',
                'comment', 'name', 'operator', 'stx', 'srx', 'state',
                'country', 'cont', 'dxcc', 'cqz', 'ituz', 'lat', 'lon'
        ]:
            strbuf = str(self.recv_buffer)
            search_token = "<" + token + ":"
            start = strbuf.lower().find(search_token)
            if start == -1:
                continue
            end = strbuf.find(':', start) - 1
            if end == -1:
                break
            pos = end + 2
            found_num = True
            while found_num is True:
                if strbuf[pos + 1].isdigit() is True:
                    pos = pos + 1
                else:
                    found_num = False

            attr_len = int(strbuf[end + 2:pos + 1])
            strbuf = str(self.recv_buffer)
            attr = strbuf[pos + 2:pos + 2 + int(attr_len)]
            # print("%s: %s" % (token, attr))
            if not attr:
                continue

            if token == 'call':
                self.call = attr
            elif token == 'gridsquare':
                self.gridsquare = attr
            elif token == 'mode':
                self.mode = attr
            elif token == 'rst_sent':
                self.rst_sent = attr
            elif token == 'rst_rcvd':
                self.rst_rcvd = attr
            elif token == 'qso_date':
                self.qso_date = attr
            elif token == 'time_on':
                self.time_on = attr
            elif token == 'time_off':
                self.time_off = attr
            elif token == 'band':
                self.band = attr
            elif token == 'freq':
                self.freq = attr
            elif token == 'station_callsign':
                self.station_callsign = attr
            elif token == 'my_gridsquare':
                self.my_gridsquare = attr
            elif token == 'tx_pwr':
                self.tx_power = attr
            elif token == 'comment':
                self.comments = attr
            elif token == 'name':
                self.name = attr
            elif token == 'operator':
                self.operator = attr
            elif token == 'state':
                self.state = attr
            elif token == 'country':
                self.country = attr
            elif token == 'cont':
                self.cont = attr
            elif token == 'dxcc':
                self.dxcc = attr
            elif token == 'cqz':
                self.cqz = attr
            elif token == 'ituz':
                self.ituz = attr
            elif token == 'lat':
                self.lat = attr
            elif token == 'lon':
                self.lon = attr

    def udp_recv_string(self):
        """ Receive text string over UDP socket """
        try:
            self.recv_buffer = ""
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((self.config['DEFAULT']['WSJT_X_HOST'],
                       int(self.config['DEFAULT']['WSJT_X_PORT'])))
            print("Waiting for new log entry...")
            self.recv_buffer = sock.recvfrom(1024)
            print("Received log message:\n\n", self.recv_buffer)
        except KeyboardInterrupt:
            sys.stderr.write("User cancelled.")
            sock.close()
            sys.exit(0)
        except socket.error as msg:
            sys.stderr.write(
                "[ERROR] %s (is another copy of wsjtx_to_Cloudlog running?)\n" %
                msg)
            sys.exit(2)

    def log_new_qso(self):
        """ Log new QSO to Cloudlog """
        data = {"key": self.cloudlog_key,
                "station_profile_id": self.cloudlog_station_id,
                "type": "adif",
                "string": "<call:" + str(len(self.call)) + ">" + self.call +
                "<band:" + str(len(self.band)) + ">" + self.band +
                "<mode:" + str(len(self.mode)) + ">" + self.mode +
                "<freq:" + str(len(self.freq)) + ">" + self.freq +
                "<qso_date:" + str(len(self.qso_date)) + ">" + self.qso_date +
                "<time_on:" + str(len(self.time_on)) + ">" + self.time_on +
                "<time_off:" + str(len(self.time_off)) + ">" + self.time_off +
                "<rst_rcvd:" + str(len(self.rst_rcvd)) + ">" + self.rst_rcvd +
                "<rst_sent:" + str(len(self.rst_sent)) + ">" + self.rst_sent +
                "<qsl_rcvd:1>N<qsl_sent:1>N" +
                "<country:" + str(len(self.country)) + ">" + self.country +
                "<gridsquare:" + str(len(self.gridsquare)) + ">" + self.gridsquare +
                "<comment:" + str(len(self.comment)) + ">" + self.comment +
                "<cont:" + str(len(self.cont)) + ">" + self.cont +
                "<country:" + str(len(self.country)) + ">" + self.country +
                "<dxcc:" + str(len(self.dxcc)) + ">" + self.dxcc +
                "<cqz:" + str(len(self.cqz)) + ">" + self.cqz +
                "<ituz:" + str(len(self.ituz)) + ">" + self.ituz +
                "<lat:" + str(len(self.lat)) + ">" + self.lat +
                "<lon:" + str(len(self.lon)) + ">" + self.lon +
                "<eor>"
                }
        print(data)
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, qso, self.cloudlog_uri, data)
        #qso(self.cloudlog_uri, data)

#         if self.contest == 'FD':
#             command = """<CMD><ADDDIRECT><EXCLUDEDUPES>TRUE</EXCLUDEDUPES>
# <STAYOPEN>TRUE</STAYOPEN>
# <fldComputerName>%s</fldComputerName>
# <fldOperator>%s</fldOperator>
# <fldNameS>%s</fldNameS>
# <fldInitials>%s</fldInitials>
# <fldCountyS>%s</fldCountyS>
# <fldCall>%s</fldCall>
# <fldNameR>%s</fldNameR>
# <fldDateStr>%s</fldDateStr>
# <fldTimeOnStr>%s</fldTimeOnStr>
# <fldTimeOffStr>%s</fldTimeOffStr>
# <fldBand>%s</fldBand>
# <fldMode>%s</fldMode>
# <fldFrequency>%s</fldFrequency>
# <fldPower>%s</fldPower>
# <fldGridR>%s</fldGridR>
# <fldGridS>%s</fldGridS>
# <fldComments>%s</fldComments>
# <fldPoints>%s</fldPoints>
# <fldClass>%s</fldClass>
# <fldSection>%s</fldSection></CMD>\r\n""" % (self.computer_name, self.operator,
#                                             self.name_s, self.initials,
#                                             self.county, self.call,
#                                             self.name_r, self.date,
#                                             self.time_on, self.time_off,
#                                             self.band, self.mode,
#                                             self.frequency, self.power,
#                                             self.grid_r, self.grid_s,
#                                             self.comments, self.points,
#                                             self.arrl_class_r,
#                                             self.arrl_section_r)
#         else:
#             command = """<CMD><ADDDIRECT><EXCLUDEDUPES>TRUE</EXCLUDEDUPES>
# <STAYOPEN>TRUE</STAYOPEN>
# <fldComputerName>%s</fldComputerName>
# <fldOperator>%s</fldOperator>
# <fldNameS>%s</fldNameS>
# <fldInitials>%s</fldInitials>
# <fldCountyS>%s</fldCountyS>
# <fldCall>%s</fldCall>
# <fldNameR>%s</fldNameR>
# <fldDateStr>%s</fldDateStr>
# <fldTimeOnStr>%s</fldTimeOnStr>
# <fldTimeOffStr>%s</fldTimeOffStr>
# <fldBand>%s</fldBand>
# <fldMode>%s</fldMode>
# <fldFrequency>%s</fldFrequency>
# <fldPower>%s</fldPower>
# <fldRstR>%s</fldRstR>
# <fldRstS>%s</fldRstS>
# <fldGridR>%s</fldGridR>
# <fldGridS>%s</fldGridS>
# <fldComments>%s</fldComments>
# <fldPoints>%s</fldPoints>
# <fldClass>%s</fldClass>
# <fldSection>%s</fldSection></CMD>\r\n""" % (self.computer_name, self.operator,
#                                             self.name_s, self.initials,
#                                             self.county, self.call,
#                                             self.name_r, self.date,
#                                             self.time_on, self.time_off,
#                                             self.band, self.mode,
#                                             self.frequency, self.power,
#                                             self.rst_r, self.rst_s,
#                                             self.grid_r, self.grid_s,
#                                             self.comments, self.points,
#                                             self.arrl_class_r,
#                                             self.arrl_section_r)
#         print("\nSending log entry to Cloudlog...")
#         print(command)
#         try:
#             sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             sock.connect((self.config['DEFAULT']['Cloudlog_HOST'],
#                           int(self.config['DEFAULT']['Cloudlog_PORT'])))
#             self.tcp_send_string(sock, command)
#             time.sleep(.2)
#             command = "<CMD><CHECKLOG></CMD>\r\n"
#             print("Sending log refresh...")
#             self.tcp_send_string(sock, command)
#             sock.close()
#         except socket.error as msg:
#             sys.stderr.write("[ERROR] Failed to connect to Cloudlog: %s\n" % msg)


if __name__ == "__main__":
    W = WsjtxToCloudlog()
    print("WSJT-X to Cloudlog by Joeri Van Dooren ON3URE\n")
    while True:
        W.udp_recv_string()
        W.parse_adif()
        W.log_new_qso()
        W.reset_vals()
    W.sock.close()

loop = asyncio.get_event_loop()
try:
    loop.run_forever()
finally:
    loop.close()
