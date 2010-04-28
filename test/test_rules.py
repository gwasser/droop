#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' 
Unit test for droop.rules package

Copyright 2010 by Jonathan Lundell

This file is part of Droop.

    Droop is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Droop is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Droop.  If not, see <http://www.gnu.org/licenses/>.
'''
import unittest
import sys, os
path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if path not in sys.path: sys.path.insert(0, os.path.normpath(path))

from droop import electionRuleNames, electionRule
from droop import rules as R
from droop.common import UsageError

class RuleInitTest(unittest.TestCase):
    "test rules.__init__"
    
    def testRuleNames(self):
        "check the list of names"
        self.assertTrue(len(electionRuleNames()) >= 4, 'at least four rule names')

    def testRuleNameMpls(self):
        "check the list of names for mpls"
        self.assertTrue('mpls' in electionRuleNames(), 'one of the rule names is mpls')

    def testElectionRule(self):
        "look up one election rule"
        from droop.rules.mpls import Rule as Mpls
        self.assertEqual(electionRule('mpls'), Mpls, 'the mpls Rule should match its name lookup')


class RuleTest(unittest.TestCase):
    "test rules class methods"
    
    def testMethod(self):
        "method is meek or wigm for each rule"
        for name in electionRuleNames():
            Rule = electionRule(name)
            method = Rule.method()
            self.assertTrue(method in ('meek','wigm'), 'bad method "%s"' % method)

    def testReportHelps(self):
        "helps gives us back a string"
        for name in electionRuleNames():
            Rule = electionRule(name)
            helps = dict()
            Rule.helps(helps, name)
            self.assertTrue(isinstance(helps[name], str), 'expected help string for %s' % name)

    def testMeekPrf(self):
        "meek-prf requires fixed"
        Rule = electionRule('prf-meek-basic')
        self.assertRaises(UsageError, Rule.options, dict(arithmetic='guarded'))

    def testMeekWarren1(self):
        "meek responds to warren"
        Rule = electionRule('warren')
        Rule.options(dict(rule='warren'))
        self.assertEqual(Rule.tag(), 'warren-generic-o9')
        self.assertRaises(UsageError, Rule.options, dict(defeat_batch='whatever'))


if __name__ == '__main__':
    unittest.main()