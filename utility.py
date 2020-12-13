import os
import re
import shutil


def calbr_controller_command_usage():
    print("Usage: ")
    print("       calbr-controller concat  serial-numbers")
    print("       calbr-controller execute sensors=in,out operands=11,22,33 temperatures=125 serial-numbers")
    print("       calbr-controller deploy  serial-numbers")


def concat_calibrates(dest, pres, flow):
    """
    join two calibrates files together
    """
    if not os.path.exists(dest):
        print("Concat calibrates: dest given not exist: %s" % os.path.basename(dest))
        return False
    if not os.path.isdir(dest):
        print("Concat calibrates: dest given not a directory: %s" % os.path.basename(dest))
        return False
    if not os.path.exists(pres):
        print("Concat calibrates: pres file not exist: %s" % os.path.basename(pres))
        return False
    if not os.path.isfile(pres):
        print("Concat calibrates: pres file not regular: %s" % os.path.basename(pres))
        return False
    if not os.path.exists(flow):
        print("Concat calibrates: flow file not exist: %s" % os.path.basename(flow))
        return False
    if not os.path.isfile(flow):
        print("Concat calibrates: flow file not regular: %s" % os.path.basename(flow))
        return False

    target = os.path.basename(pres).replace('.p', '.')
    print("Concat calibrates: %s   ....    " % target, end='')
    with open(pres, 'r') as pres_reader, \
            open(flow, 'r') as flow_reader, \
            open(os.path.join(dest, target), 'w') as writer:
        writer.write(pres_reader.read())
        writer.write(flow_reader.read())

    if os.path.getsize(os.path.join(dest, target)) == 0:
        print("Failure")
        return False

    print("Success")
    return True


def parse_serial_numbers(*args):
    """
    parse command line input to get serial numbers wanted
    """
    if not args:
        return []

    serial_numbers = []
    for arg in args:
        if re.match(r'^\d{3,5}$', arg):
            serial_numbers.append(arg)
        elif re.match(r'\d{3,5}[-~:]\d{3,5}', arg):
            references = re.split(r'[-~:]', arg)
            if len(references[0]) != len(references[1]):
                serial_numbers.extend([references[0], references[1]])
            else:
                start = min(int(references[0]), int(references[1]))
                final = max(int(references[0]), int(references[1]))
                for number in range(start, final+1):
                    serial_numbers.append(str(number))
    return serial_numbers


def copy_calibrates(serial_numbers, src, dest, pres=True, flow=True):
    """
    copy calibrates files that begin with @serial_numbers from @src to @dest
    """
    # parameter checks
    if not serial_numbers:
        print("copy_calibrates: serial numbers given empty")
        return
    if not os.path.exists(src):
        print("copy_calibrates: src given not exist")
        return
    if not os.path.isdir(src):
        print("copy_calibrates: src given not directory")
        return
    if not os.path.exists(dest):
        print("copy_calibrates: dest given not exist")
        return
    if not os.path.isdir(dest):
        print("copy_calibrates: dest given not directory")
        return

    pres_files = []
    flow_files = []
    for serial in serial_numbers:
        pres_files.append(str(serial) + ".pCal")
        flow_files.append(str(serial) + ".fCal")

    calibrates = os.listdir(src)
    for filename in pres_files:
        print("Copying calibrate:  %s   ....    " % filename, end='')
        # check whether file needed exists
        try:
            calibrates.index(filename)
        except ValueError as e:
            print("Missing")
            continue
        # now, do the copy
        try:
            shutil.copy(os.path.join(src, filename), dest)
        except (IOError, OSError) as e:
            print("Failure")
            continue
        print("Success")

    for filename in flow_files:
        print("Copying calibrate:  %s   ....    " % filename, end='')
        # check whether file needed exists
        try:
            calibrates.index(filename)
        except ValueError as e:
            print("Missing")
            continue
        # now, do the copy
        try:
            shutil.copy(os.path.join(src, filename), dest)
        except (IOError, OSError) as e:
            print("Failure")
            continue
        print("Success")


def copy_linearfits(serial_numbers, src, dest):
    """
    copy linearfits files that start with @serial_numbers from @src to @dest
    """
    if not serial_numbers:
        print("copy_linearfits: serial numbers given empty")
        return
    if not os.path.exists(src):
        print("copy_linearfits: src given not exist")
        return
    if not os.path.isdir(src):
        print("copy_linearfits: src given not directory")
        return
    if not os.path.exists(dest):
        print("copy_linearfits: dest given not exist")
        return
    if not os.path.isdir(dest):
        print("copy_linearfits: dest given not directory")
        return

    linearfits = os.listdir(src)
    pattern = '^ZCF-301B\s+ST(?P<serial>\d{3,5})'
    linearfits_serials = []
    # Mapping linearfits to serials, one on one, match for 'serial number', not match for ''
    for filename in linearfits:
        solution = re.search(pattern, filename)
        if solution:
            linearfits_serials.append(solution.group('serial'))
        else:
            linearfits_serials.append('')

    for serial in serial_numbers:
        print("Copying linearfit:  %s(xls)   ....    " % serial, end='')
        # Check whether file needed exists
        try:
            index = linearfits_serials.index(serial)
        except ValueError as e:
            print("Missing")
            continue

        # Now, do the copy
        try:
            shutil.copy(os.path.join(src, linearfits[index]), dest)
        except (IOError, OSError) as e:
            print("Failure")
            continue
        print("Success")
