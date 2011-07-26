#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import exists, join, abspath, sep, splitext, dirname
from json import dumps

from provy.core import Role

import os
import fnmatch
import inspect


class RoleDoc(object):
    def __init__(self, role, name, module, docs):
        self.role = role
        self.name = name
        self.module = module
        self.fullname = "%s.%s" % (module, name)
        self.docs = docs
        self.methods = []
        self.parse_methods(role)

    def parse_methods(self, role):
        for name, member in inspect.getmembers(role):
            if not inspect.ismethod(member) or name.startswith('_'):
                continue
            if not member.__module__ == role.__module__:
                continue
            if not member.__doc__:
                print "Warning: Method %s of role %s does not have docstring." % (name, role.__name__)
            self.add_method(NameDoc(name, member.__doc__))

    def add_method(self, method_doc):
        self.methods.append(method_doc)

    def to_dict(self):
        obj = {
            '__name__': self.name,
            '__fullName__': self.fullname,
            '__module__': self.module,
            '__doc__': self.docs and self.docs.strip() or None,
            '__methods__': []
        }
        for method in self.methods:
            obj['__methods__'].append(method.to_dict())

        return obj


class NameDoc(object):
    def __init__(self, name, doc):
        self.name = name
        self.doc = doc

    def to_dict(self):
        return {
            '__name__': self.name,
            '__doc__': self.doc and self.doc.strip() or None
        }


def main():
    path = "/tmp/docs.json"
    source_path = join(os.curdir, 'provy', 'more')

    if not exists(dirname(path)):
        os.makedirs(dirname(path))

    root_namespace = 'provy.more'

    roles_to_document = {
        'Role': RoleDoc(Role, 'Role', 'provy.core.roles', Role.__doc__)
    }

    for root, dirs, files in os.walk(source_path):
        for file_name in files:
            if file_name == "__init__.py":
                continue
            if not fnmatch.fnmatch(file_name, '*.py'):
                continue

            module_path = '%s.%s.%s' % (root_namespace,
                                        get_namespace_for(root),
                                        splitext(file_name)[0])

            module = import_module(module_path)

            for name, member in inspect.getmembers(module):
                if not inspect.isclass(member) or not issubclass(member, Role):
                    continue
                if member.__module__ != module_path:
                    continue

                if not member.__doc__:
                    print "Warning: Role %s.%s does not have docstring." % (member.__module__, name)

                roles_to_document[module_path] = RoleDoc(member,
                                                         name,
                                                         member.__module__,
                                                         member.__doc__)

    tree = {}

    for full_name, role_doc in roles_to_document.iteritems():
        role = role_doc.role
        name = role_doc.name
        current = tree
        module = __import__(role.__module__)
        for part in role.__module__.split('.'):
            if hasattr(module, part):
                module = getattr(module, part)
            if not part in current:
                if not module.__doc__:
                    print "Warning: Module %s does not have docstring." % module.__name__

                current[part] = {
                    '__name__': module.__name__,
                    '__doc__': module.__doc__ and module.__doc__.strip() or None
                }
            if part == role.__module__.split('.')[-1]:
                current[part][role_doc.name] = role_doc.to_dict()
            current = current[part]

    contents = dumps(tree, sort_keys=True, separators=(',', ':'))
    with open(path, 'w') as f:
        f.write(contents)


def import_module(module_path):
    module = __import__(module_path)
    return reduce(getattr, module_path.split('.')[1:], module)


def get_namespace_for(directory):
    source_path = abspath(join(os.curdir, 'provy', 'more'))
    diff = abspath(directory).replace(source_path, '')
    namespace = '.'.join([module for module in diff.split(sep) if module])
    return namespace

if __name__ == '__main__':
    main()
