#!/usr/bin/python
# -*- coding: utf-8 -*-

##################################
# Standard library imports
##################################

import os
import datetime
from unittest import TestCase

##################################
# Custom library imports
##################################

from tzwhere import tzwhere
from tzwhere.tzwhere import BASE_DIR


####################################

class TestTzwhereUtilities(TestCase):
    def test_preparemap_class(self):
        """
        Tests the prepareMap class which writes shortcuts file.  Test looks
        at modified date to see if that's equivalent to today's date

        :return:
        Unit test response
        """

        a = tzwhere.prepareMap()
        location = os.path.join(BASE_DIR, 'tzwhere', 'tz_world_shortcuts.json')
        date = datetime.datetime.now().date()
        modified = datetime.datetime. \
            fromtimestamp(os.stat(location).st_mtime).date()
        return self.assertEqual(date, modified)
