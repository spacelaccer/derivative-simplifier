import os
import re
import sys
import shutil
import datetime

import utility


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


def make_linearfits_callback(parser, *args, **kwargs):
    """
    Move derivative needed linearfits to directory @linearfits for making derivative,
    because linearfits are not used frequently, they are moved to @linearfits for storing.
    """
    # We have nowhere to find the target linearfits
    if not hasattr(parser, 'src_linearfits') and 'src' not in kwargs:
        return

    source = ''
    if 'src' in kwargs:
        source = kwargs['src']
    else:
        source = parser.src_linearfits
    if not os.path.isdir(source):
        print("Fatal Error: %s: not directory" % source)
        return

    base = os.path.join(parser.root, parser.linearfits)
    if not args:
        for filename in os.listdir(source):
            if re.match(parser.lin_pattern, filename):
                print("Moving linearfit:   %s    ....    " % filename[:20], end='')
                try:
                    shutil.move(os.path.join(source, filename), base)
                except (IOError, OSError) as e:
                    print("Failure")
                    continue
                print("Success")
        return

    serial_numbers = utility.parse_serial_numbers(*args)
    for linearfit in os.listdir(source):
        solution = re.match(parser.lfit_pattern, linearfit)
        if solution:
            serial = solution.group('serial_number')
            if serial in serial_numbers:
                print("Moving linearfit:   %s    ....    " % linearfit[:20], end='')
                try:
                    shutil.move(os.path.join(source, linearfit), base)
                except (OSError, IOError) as e:
                    print("Failure")
                    continue
                print("Success")
                serial_numbers.remove(serial)

    # Check whether there are any serials left
    if serial_numbers:
        for serial in serial_numbers:
            linearfit = "ZCF-301B ST" + serial + "流量系数"
            print("Moving linearfit:   %s    ....    " % linearfit, end='')
            print("Missing")


def make_calibrates_callback(parser, *args, **kwargs):
    """
    Copy derivative needed calibrates to directory @calibrates for making derivative,
    source calibrates always reside somewhere outside our root directory but within
    a software's secondary directory, and they are frequently needed, so they will just
    be copied, not moved. The path is recorded in @config.cfg, and has been read by @parser,
    if it is not recorded, nothing will be done.
    """
    # we do not know where to find the source calibrates
    if not hasattr(parser, 'src_calibrates') and 'src' not in kwargs:
        return

    source = ''
    if 'src' in kwargs:
        source = kwargs['src']
    else:
        source = parser.src_calibrates
    if not os.path.isdir(source):
        print("Fatal Error: %s: not directory" % source)
        return

    # Location where we copy source calibrates to
    base = os.path.join(parser.root, parser.calibrates)
    # If no serial numbers specified, just copy them all
    if not args:
        for filename in os.listdir(source):
            if re.match(parser.cal_pattern, filename):
                print("Copying calibrate:   %s    ....    " % filename, end='')
                try:
                    shutil.copy(os.path.join(source, filename), base)
                except (IOError, OSError) as e:
                    print("Failure")
                    continue
                print("Success")
        return

    # Serial numbers specified
    serial_numbers = utility.parse_serial_numbers(*args)
    calibrates = os.listdir(source)
    candidates = []
    # Create list contains all calibrates being copied
    for serial in serial_numbers:
        candidates.append(serial + '.pCal')
        candidates.append(serial + '.fCal')
    for candidate in candidates:
        print("Copying calibrate:   %s    ....    " % candidate, end='')
        if candidate not in calibrates:
            print("Missing")
            continue
        try:
            shutil.copy(os.path.join(source, candidate), base)
        except (OSError, IOError) as e:
            print("Failure")
            continue
        print("Success")


def make_derivative_callback(parser, *args, **kwargs):
    """
    make derivative packages
    """
    serial_numbers = []
    if args:
        # Retrieve serial numbers given in command line
        serial_numbers = utility.parse_serial_numbers(*args)
        # Copy calibrates essential to specified location
        utility.copy_calibrates(serial_numbers,
                                os.path.join(parser.root, parser.calibrates),
                                os.path.join(parser.root, parser.laboratory))
        # Copy linearfits essential to specified location
        utility.copy_linearfits(serial_numbers,
                                os.path.join(parser.root, parser.linearfits),
                                os.path.join(parser.root, parser.laboratory))
        # Separating copy operation messages and make operation messages
        print()

    # Dict to save file information
    made_derivative = {}
    pres_calibrates = {}
    flow_calibrates = {}
    lfit_linearfits = {}

    # Collect essential file information
    for filename in os.listdir(parser.laboratory):
        solution = re.match(parser.pres_pattern, filename)
        if solution:
            pres_calibrates.update({solution.group('serial_number'): {'filename': filename}})
            if not args and solution.group('serial_number') not in serial_numbers:
                serial_numbers.append(solution.group('serial_number'))
    for filename in os.listdir(parser.laboratory):
        solution = re.match(parser.flow_pattern, filename)
        if solution:
            flow_calibrates.update({solution.group('serial_number'): {'filename': filename}})
            if not args and solution.group('serial_number') not in serial_numbers:
                serial_numbers.append(solution.group('serial_number'))
    for filename in os.listdir(parser.laboratory):
        solution = re.match(parser.lfit_pattern, filename)
        if solution:
            lfit_linearfits.update({solution.group('serial_number'): {
                'filename': filename,
                'volume': solution.group('serial_volume')
            }})
            if not args and solution.group('serial_number') not in serial_numbers:
                serial_numbers.append(solution.group('serial_number'))

    # Collecting derivatives related information
    base = os.path.join(parser.root, parser.laboratory)
    timestamp = datetime.datetime.now().strftime('%Y.%m.%d')
    for serial in serial_numbers:
        missing_message = []   # recording what are the missing files
        made_derivative.update({serial: {}})
        if serial in pres_calibrates:
            made_derivative[serial].update({'pres': pres_calibrates[serial]['filename']})
        else:
            missing_message.append("pres")

        if serial in flow_calibrates:
            made_derivative[serial].update({'flow': flow_calibrates[serial]['filename']})
        else:
            missing_message.append("flow")

        if serial in lfit_linearfits:
            made_derivative[serial].update({'lfit': lfit_linearfits[serial]['filename']})
        else:
            missing_message.append("lfit")

        if made_derivative[serial].__contains__('pres') and \
            made_derivative[serial].__contains__('flow') and \
            made_derivative[serial].__contains__('lfit'):
            derv = "ZCF-301B ST{serial}({timestamp}){volume}".format(serial=serial, timestamp=timestamp,
                                                                     volume=lfit_linearfits[serial]['volume'])
            made_derivative[serial].update({'status': True})
        else:
            derv = 'ZCF-301B ST{serial}({timestamp})'.format(serial=serial, timestamp=timestamp)
            made_derivative[serial].update({'status': False})
            error = 'Missing ' + ', '.join(missing_message)
            made_derivative[serial].update({'error': error})

        made_derivative[serial].update({'derv': derv})

    # Starting making derivative
    for serial in serial_numbers:
        target = os.path.join(base, made_derivative[serial]['derv'])
        # For beauty, just output part of the name of derivative of it's too long
        print("Making derivative:  %s   ....    " % made_derivative[serial]['derv'][0:28], end='')

        # If there are files missing, go to next
        if not made_derivative[serial]['status']:
            print(made_derivative[serial]['error'])
            continue

        # No files missing, begin making
        try:
            os.mkdir(target)
        except OSError as e:
            print("Failure")
            continue
        try:
            shutil.move(os.path.join(base, made_derivative[serial]['pres']), target)
            shutil.move(os.path.join(base, made_derivative[serial]['flow']), target)
            shutil.move(os.path.join(base, made_derivative[serial]['lfit']), target)
        except (IOError, OSError) as e:
            print("Failure")
            continue

        print("Success")
