import os
import sys
import callback
from parser import CommandElementParser


command_prompt = ">>> "

if __name__ == '__main__':

    parser = CommandElementParser()
    parser.append_element('exit',
                          callback=callback.exit_callback,
                          description='Just exit')
    parser.append_element('quit',
                          callback=callback.exit_callback,
                          description='Just quit')
    parser.append_element('help',
                          callback=callback.help_callback,
                          description='Show useful information')
    parser.append_element('make-derivative', 'makeder',
                          callback=callback.make_derivative_callback,
                          description='Make derivative package')
    while True:
        command = input(command_prompt)
        parser.parse(command)
