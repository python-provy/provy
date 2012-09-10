#!/usr/bin/env python

from pprint import pformat

from pyvows import Vows


@Vows.assertion
def to_have_been_called(function):
    assert len(function.calls) > 0


@Vows.assertion
def to_have_been_called_with(function, *args, **kwargs):
    be_called = False
    for call in function.calls:
        if call['args'] == args and call['kwargs'] == kwargs:
            be_called = True
    assert be_called, "The function should be called with %s, %s, but was not. Calls were:\n%s" % (str(args), str(kwargs), pformat(function.calls))


@Vows.assertion
def to_have_been_called_like(function, *args):
    be_called = False
    for call in function.calls:
        if call['args'] == args:
            be_called = True
    assert be_called


@Vows.assertion
def not_to_have_been_called(function):
    assert len(function.calls) == 0


@Vows.assertion
def to_have_attr(obj, attr_name):
    assert hasattr(obj, attr_name)


@Vows.assertion
def to_be(obj, type_class):
    assert type(obj) == type_class or isinstance(obj, type_class) or obj == type_class


@Vows.assertion
def not_to_be(obj, type_class):
    assert type(obj) != type_class and not isinstance(obj, type_class) and obj != type_class


@Vows.assertion
def to_have_key(dict_obj, key):
    assert key in dict_obj

