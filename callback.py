import os
import re
import sys
import shutil
import datetime


def exit_callback(parser, *args, **kwargs):
    """
    exit main infinitive loop
    """
    sys.exit(0)


def quit_callback(parser, *args, **kwargs):
    """
    exit main infinitive loop
    """
    sys.exit(0)


def help_callback(parser, *args, **kwargs):
    """
    list help information
    """
    max_command_columns = parser.get_max_command_length()
    for command in parser.elements():
        print(command.command, end='   ')
        if len(command.command) < max_command_columns:
            print((max_command_columns-len(command.command)) * ' ', end='')
        print(command.description)


def make_derivative_callback(parser, *args, **kwargs):
    """
    make derivative packages
    """
    if not args:
        print("No serial number given, nothing done")
        return

    # Retrieve serial numbers given in command line
    serial_numbers = []
    for arg in args:
        if re.match(r'^\d{3,5}$', arg):
            serial_numbers.append(arg)
        elif re.match(r'\d{3,5}[-~:]\d{3,5}', arg):
            references = re.split(r'[-~:]', arg)
            if len(references[0]) != len(references[1]):
                serial_numbers.append(references[0])
                serial_numbers.append(references[1])
            else:
                start = min(int(references[0]), int(references[1]))
                final = max(int(references[0]), int(references[1]))
                for number in range(start, final+1):
                    serial_numbers.append(str(number))
    print(serial_numbers)

    # Dict to save file information
    made_derivative = {}
    pres_calibrates = {}
    flow_calibrates = {}
    lfit_linearfits = {}

    # Regular expression patterns to recognize filenames
    pres_pattern = r'^(?P<serial_number>\d{4,5})[.]pCal$'
    flow_pattern = r'^(?P<serial_number>\d{4,5})[.]fCal$'
    lfit_pattern = r'^ZCF-301B\s+ST(?P<serial_number>\d{4,5})\w{4,}(?P<serial_volume>-?\w{0,3})[.]xls$'
    derv_pattern = r'^ZCF-301B\s+ST\d{3,5}\(\d{4}[.]\d{2}[.]\d{2}\)-?\w{0,3}$'

    # Collect essential file information
    for filename in os.listdir(path_calibrates):
        match_result = re.match(pres_pattern, filename)
        if match_result:
            pres_calibrates.update({match_result.group('serial_number'): {'filename': filename}})
    for filename in os.listdir(path_calibrates):
        match_result = re.match(flow_pattern, filename)
        if match_result:
            flow_calibrates.update({match_result.group('serial_number'): {'filename': filename}})

    for filename in os.listdir(path_linearfits):
        match_result = re.match(lfit_pattern, filename)
        if match_result:
            lfit_linearfits.update({match_result.group('serial_number'): {
                'filename': filename,
                'volume': match_result.group('serial_volume')
            }})

    # Get names of derivative packages done
    timestamp = datetime.datetime.now().strftime('%Y.%m.%d')
    for serial in serial_numbers:
        made_derivative.update({serial: {}})
        if serial in pres_calibrates:
            made_derivative[serial].update({'pres': pres_calibrates[serial]['filename']})
        if serial in flow_calibrates:
            made_derivative[serial].update({'flow': flow_calibrates[serial]['filename']})
        if serial in lfit_linearfits:
            made_derivative[serial].update({'lfit': lfit_linearfits[serial]['filename']})

        if made_derivative[serial].__contains__('pres') and \
            made_derivative[serial].__contains__('flow') and \
            made_derivative[serial].__contains__('lfit'):
            derv = "ZCF-301B ST{serial}({timestamp}){volume}".format(serial=serial, timestamp=timestamp,
                                                                     volume=lfit_linearfits[serial]['volume'])
            made_derivative[serial].update({'derv': derv})