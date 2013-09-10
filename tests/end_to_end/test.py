#!/usr/bin/env python

import os
from unittest import TestCase

from nose.tools import istest
import requests


class EndToEndTests(TestCase):
    @istest
    def gets_response_from_tornado(self):
        response = requests.get('http://{}:{}'.format(os.environ['PROVY_HOST'], os.environ['PROVY_PORT']))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Hello, world')
