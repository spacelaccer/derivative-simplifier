import os
import sys
import callback
from parser import CommandElementParser


command_prompt = ">>> "

if __name__ == '__main__':

    parser = CommandElementParser()
    parser.parse_config()
    parser.append_element('exit',
                          callback=callback.exit_callback,
                          description='Just exit')
    parser.append_element('quit',
                          callback=callback.exit_callback,
                          description='Just quit')
    parser.append_element('help',
                          callback=callback.help_callback,
                          description='Show useful information')
    parser.append_element('make-calibrates', 'makeclr', 'makeclb',
                          prototype={'src': 'str'},
                          callback=callback.make_calibrates_callback,
                          description='Copy calibrates to storage location designated')
    parser.append_element('make-linearfits', 'makelft', 'makelin',
                          prototype={'src': 'str'},
                          callback=callback.make_linearfits_callback,
                          description='Copy linearfits to storage location designated')
    parser.append_element('make-derivative', 'makeder', 'makedev', 'makedet',
                          callback=callback.make_derivative_callback,
                          description='Make derivative package')
    while True:
        command = input(command_prompt)
        parser.parse(command)
