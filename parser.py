import abc
import os
import re
import configparser
from typing import Union, List, Optional


def _parse_number(value: str, type_cls) -> int:
    """
    value starts with 0x is hexadecimal, with 0b is binary,
    with 0 is octal, else it is decimal
    :param value:
    :param type_cls:
    :return:
    """
    if value[:2].lower() == '0x':
        base = 16
    elif value[:2].lower() == '0b':
        base = 2
    elif value[:1] == '0':
        base = 8
    else:
        base = 10

    return type_cls(value, base)


def parse_int(value: Optional[str]):
    return _parse_number(value, int)


def parse_bool(value: Optional[Union[str, bool]]):
    if isinstance(value, bool):
        return value

    if value.lower() == 'true':
        return True
    elif value.lower() == 'yes':
        return True
    elif value.lower() == 'false':
        return False
    elif value.lower() == 'no':
        return False
    else:
        raise Exception('%s: unknown value' % repr(value))


def parse_type(type_str: str):
    if type_str.lower() == 'str':
        return str
    elif type_str.lower() == 'int':
        return int
    elif type_str.lower() == 'bool':
        return bool
    else:
        raise Exception('%s: unknown type string' % repr(type_str))


def contains_characters(string: str, characters: str) -> bool:
    if not string:
        return False

    if not characters:
        return False

    for char in characters:
        if char in string:
            return True
    return False


class Element(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def conflict_handler(cls, element, identifier: Union[str, List]) -> bool:
        """
        Check whether there are elements with the same value
        """

    @abc.abstractmethod
    def acquire_identifier(self):
        """
        return identifier of given element
        """

    @abc.abstractmethod
    def acquire_description(self):
        """
        return description of element
        """

    @abc.abstractmethod
    def confirm_identifier(self, identifier: Union[str, List]) -> bool:
        """
        Check whether our element has the same identifier with the given one
        """


class CommandElement(Element):

    ALL_ATTRS = [
        'command',
        'abbrevs',
        'prototype',
        'defaults',
        'callback',
        'callback_args',
        'callback_kwargs',
        'description',
    ]

    BASE_ATTRS = [
        'prototype',
        'defaults',
        'callback',
        'description',
    ]

    DEFAULT_VALUES = {
        'str': '',
        'int': 0,
        'bool': False,
        'list': [],
        'dict': {},
        'tuple': (),
        'float': 0.0,
    }

    TYPE_PARSER = {
        'int': parse_int,
        'bool': parse_bool,
    }

    @classmethod
    def conflict_handler(cls, element, identifier: Union[str, List]) -> bool:
        if not isinstance(element, cls):
            return True
        if isinstance(identifier, str):
            if identifier in element.abbrevs:
                return True
        if isinstance(identifier, list):
            for identity in identifier:
                if identity in element.abbrevs:
                    return True
        return False

    def __init__(self, *args, **kwargs):
        self.command = ''
        self.abbrevs = []
        self.prototype = {}
        self.defaults = {}
        self.callback = None
        self.callback_args = []
        self.callback_kwargs = {}
        self.description = ''

        # process arguments for command strings
        if args is None:
            raise Exception("Command string must be supplied")
        for arg in args:
            if not type(arg) == str:
                raise Exception("Command string required")
            if len(arg) < 2:
                raise Exception("Command string too short")
            if ' ' in arg:
                raise Exception("Command string contains space")

            self.abbrevs.append(arg)
            if len(arg) > len(self.command):
                self.command = arg

        # process key-value pair arguments for command attrs
        if kwargs is None:
            raise Exception("Command attributes required")
        for key in kwargs.keys():
            if key not in self.ALL_ATTRS:
                raise Exception("%s: Unknown attribute" % key)
            if key not in self.BASE_ATTRS:
                raise Exception("%s: Improper attribute" % key)

        if 'prototype' in kwargs:
            if not isinstance(kwargs['prototype'], dict):
                raise Exception("attr prototype requires dict")
            for key in kwargs['prototype'].keys():
                if not isinstance(key, str):
                    raise Exception("attr %s: string required" % key)
            for value in kwargs['prototype'].values():
                if value.strip().lower() not in self.DEFAULT_VALUES.keys():
                    raise Exception("value %s: improper type" % value)

        if 'callback' not in kwargs:
            raise Exception("callback required")
        if not callable(kwargs['callback']):
            raise Exception("callback must be callable")

        if 'defaults' in kwargs:
            if not isinstance(kwargs['defaults'], dict):
                raise Exception("attr defaults requires dict")
            for param in kwargs['defaults'].keys():
                if param not in kwargs['prototype']:
                    raise Exception("Key: %s in defaults conflicts with prototype"
                                    % param)
                if not isinstance(kwargs['defaults'][param],
                                  parse_type(kwargs['prototype'][param])):
                    raise Exception("Value: %s in defaults conflicts with prototype"
                                    % kwargs['defaults'][param])

        if 'description' in kwargs:
            if not isinstance(kwargs['description'], str):
                raise Exception("attr description requires string")

        for attr in kwargs:
            setattr(self, attr, kwargs[attr])

        if self.defaults:
            for (attr, value) in self.defaults.items():
                self.callback_kwargs.update({attr: value})

    def acquire_identifier(self):
        return self.abbrevs

    def confirm_identifier(self, identifier):
        if identifier in self.abbrevs:
            return True
        return False

    def acquire_description(self):
        return self.description

    def parse_param(self, line):
        self.callback_args.clear()
        self.callback_kwargs.clear()
        for part in line.split(' '):
            # remove possible leading or trailing separators
            part = part.strip('=,;|/')

            if '=' in part:
                attr = part.split('=')
                if len(attr) > 2:
                    raise Exception("too many = in keyword")
                self.callback_kwargs.update({attr[0]: attr[1]})
            # arguments separated by separators
            elif contains_characters(part, ',;|'):
                targets = re.split(r'[,;|]', part)
                for target in targets:
                    if target:
                        self.callback_args.append(target)
            else:
                if part:
                    self.callback_args.append(part)

    def _check_value(self, key, value):
        parser = self.TYPE_PARSER.get(self.prototype[key])
        if parser is None:
            return value
        else:
            return parser(value)

    def parse_value(self):
        for arg in self.callback_args:
            pass

        for (attr, value) in self.callback_kwargs.items():
            if attr not in self.prototype.keys():
                raise Exception("%s: unknown attr" % attr)
            value = self._check_value(attr, value)
            self.callback_kwargs.update({attr: value})

    def parse_parse(self, parser):
        self.callback(parser, *tuple(self.callback_args), **self.callback_kwargs)

    def parse_clear(self):
        self.callback_args.clear()
        self.callback_kwargs.clear()


class ElementContainer(abc.ABC):

    @abc.abstractmethod
    def elements(self):
        """
        return all elements contained in one list
        """

    @abc.abstractmethod
    def append_element(self, *args, **kwargs):
        """
        add element to container
        """

    @abc.abstractmethod
    def remove_element(self, identifier):
        """
        remove element from container
        """

    @abc.abstractmethod
    def acquire_element(self, identifier):
        """
        retrieve element from container
        """

    @abc.abstractmethod
    def contain_element(self, identifier):
        """
        check whether given element is contained in container
        """


class CommandElementContainer(ElementContainer):

    def __init__(self):
        self.container = []
        self.element_class = CommandElement
        self.maximum_command_length = 0
        self.conflict_handler = self.element_class.conflict_handler

    def elements(self):
        return self.container

    def _check_element_conflict(self, element):
        identifier = element.acquire_description()
        for element_in in self.container:
            if self.conflict_handler(element_in, identifier):
                return True
        return False

    def append_element(self, *args, **kwargs):
        element = self.element_class(*args, **kwargs)
        if not self._check_element_conflict(element):
            self.container.append(element)
            if len(element.command) > self.maximum_command_length:
                self.maximum_command_length = len(element.command)

    def remove_element(self, identifier):
        for element in self.container:
            if element.confirm_identifier(identifier):
                self.container.remove(element)
                if len(element.command) == self.maximum_command_length:
                    self.maximum_command_length = 0
                    for elem in self.container:
                        if len(elem.command) > self.maximum_command_length:
                            self.maximum_command_length = len(elem.command)


    def acquire_element(self, identifier):
        for element in self.container:
            if element.confirm_identifier(identifier):
                return element

    def contain_element(self, identifier):
        for element in self.container:
            if element.confirm_identifier(identifier):
                return True
        return False


class ElementParser(ElementContainer):
    pass

class CommandElementParser(CommandElementContainer):

    def __init__(self):
        super().__init__()
        self.config = {}

    # parse config file
    def parse_config(self):
        self.root = os.path.dirname(os.path.abspath(__file__))
        config = os.path.join(self.root, 'config.cfg')

        if not os.path.exists(config):
            raise Exception("Fatal Error: config file (config.py) not found")
        if not os.path.isfile(config):
            raise Exception("Fatal Error: config.py found, but not regular file")

        parser = configparser.ConfigParser()
        parser.read(config)

        for section in parser.sections():
            for option in parser.options(section):
                setattr(self, option, parser.get(section, option))
                print("%s: %s" % (option, getattr(self, option)))
                self.config.update({option: parser.get(section, option)})

    def get_max_command_length(self):
        return self.maximum_command_length

    def parse(self, command_input):
        if not command_input or not command_input.strip():
            return

        command_master = command_input.split(' ', 1)[0]
        command = self.acquire_element(command_master)
        if not command:    # no recognized command found
            print("%s: Command not found" % command_master)
            return

        # command recognized and to process
        command.parse_param(command_input[len(command_master):])
        command.parse_value()
        command.parse_parse(self)
        command.parse_clear()