__author__ = 'jb'

import unittest
from provy.more.debian.package.alternatives import QueryResultParser
DATA="""
Name: editor
Link: /usr/bin/editor
Slaves:
 editor.1.gz /usr/share/man/man1/editor.1.gz
 editor.fr.1.gz /usr/share/man/fr/man1/editor.1.gz
 editor.it.1.gz /usr/share/man/it/man1/editor.1.gz
 editor.pl.1.gz /usr/share/man/pl/man1/editor.1.gz
 editor.ru.1.gz /usr/share/man/ru/man1/editor.1.gz
Status: auto
Best: /bin/nano
Value: /bin/nano

Alternative: /bin/ed
Priority: -100
Slaves:
 editor.1.gz /usr/share/man/man1/ed.1.gz

Alternative: /bin/nano
Priority: 40
Slaves:
 editor.1.gz /usr/share/man/man1/nano.1.gz

Alternative: /usr/bin/vim.tiny
Priority: 10
Slaves:
 editor.1.gz /usr/share/man/man1/vim.1.gz
 editor.fr.1.gz /usr/share/man/fr/man1/vim.1.gz
 editor.it.1.gz /usr/share/man/it/man1/vim.1.gz
 editor.pl.1.gz /usr/share/man/pl/man1/vim.1.gz
 editor.ru.1.gz /usr/share/man/ru/man1/vim.1.gz
"""

class AlternativesParserTest(unittest.TestCase):

    def setUp(self):
        self.tested = QueryResultParser("editor", DATA)

    def test_name(self):
        self.assertEqual("editor", self.tested.name)

    def test_link(self):
        self.assertEqual("/usr/bin/editor", self.tested.link)

    def test_alternatives(self):
        self.assertEqual([('/bin/ed', -100), ('/bin/nano', 40), ('/usr/bin/vim.tiny', 10)], self.tested.alternatives)
