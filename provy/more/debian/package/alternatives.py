from operator import itemgetter
from fabric.context_managers import settings, hide
from provy.core import Role

__author__ = 'jb'

import re



class QueryResultParser(object):

    """
    Parses output of `update-alternatives --query link_name`
    """

    NAME_REGEXP = re.compile(ur"Name:\s*([\w\d\-./]+)\s*")
    LINK_REGEXP = re.compile(ur"Link:\s*([\w\d\-./]+)\s*")
    ALTERNATIVE_REGEXP = re.compile(ur"Alternative:\s*([^\s]+)\s*$\s*Priority:\s*([^\s]+)\s*$", re.MULTILINE)

    def __init__(self, name, data):
        super(QueryResultParser, self).__init__()
        self.data = str(data)
        self.name = name

    def has_alternative(self):
        pass

    #    @property
    #    def name(self):
    #        return re.search(self.NAME_REGEXP, self.data).group(1)

    @property
    def link(self):
        return re.search(self.LINK_REGEXP, self.data).group(1)

    @property
    def alternatives(self):
        return map(lambda x: (x[0], int(x[1])), re.findall(self.ALTERNATIVE_REGEXP, self.data))




class AlternativesRole(Role):
    """
        Role that allows using debian alternatives system.

    """

    def has_alternative(self, name):
        """
        Returns true if there is an alternative named `name` in system.
        """
        with settings(
            hide('warnings', 'running', 'stdout', 'stderr'),
            warn_only=True
        ):
            data = self.execute("update-alternatives --query {}".format(name))
            if data.return_code == 0:
                return True
            else:
                return False

    def list_alternatives(self, name):
        """
        Returns alternatives for `name` and their priorities stored in the system.

        :param name: Alternative to return alternatives for.

        :return: List of touples. First element in each tuple is alerntaive executable second is priority.
            For example [('/bin/ed', -100), ('/bin/nano', 40), ('/usr/bin/vim.tiny', 10)].

        """
        data = self.execute("update-alternatives --query {}".format(name))
        return QueryResultParser(name, data).alternatives

    def add_alternative(self, name, path_to_executable, path_to_link = None, priority = None, set_as_default = True):
        data = self.execute("update-alternatives --query {}".format(name))
        parser = QueryResultParser(name, data)
        if path_to_link is None:
            path_to_link = parser.link

        if priority is None:
            priority = max(map(itemgetter(1), parser.alternatives)) + 1

        command = "update-alternatives --install {link} {p.name} {path} {priority}".format(
            p = parser, path = path_to_executable, priority = priority, link = path_to_link
        )

        self.execute(command, stdout=False, sudo=True)

        if set_as_default:
            self.set_alternative(name, path_to_executable)

    def set_alternative(self, name, path_to_executable):

        command = "update-alternatives --set {} {}".format(name, path_to_executable)

        self.execute(command, stdout=False, sudo=True)






