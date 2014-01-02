# -*- coding: utf-8 -*-


class ConfigurationError(RuntimeError):
    '''Raised when there's a configuration error in the provyfile.'''

class CommandExecutionError(RuntimeError):
    '''
    Raised when local command has invalid exitcode
    '''
