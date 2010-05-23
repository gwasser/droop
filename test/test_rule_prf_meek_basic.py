#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' 
Unit test for droop.election package

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

from common import testdir, doDumpCompare
from droop import electionRuleNames, electionRule
from droop.election import Election
from droop.profile import ElectionProfile
from droop.common import UsageError

class RuleBasicTest(unittest.TestCase):
    "make sure we're in the book"
    
    def testElectionNames(self):
        self.assertTrue('prf-meek-basic' in electionRuleNames())

    def testArithmetic(self):
        "meek-prf requires fixed"
        Rule = electionRule('prf-meek-basic')
        self.assertRaises(UsageError, Rule.options, dict(arithmetic='guarded'))

class ElectionCountTest(unittest.TestCase):
    "test some counts"

    def doCount(self, options, blt):
        "run the count and return the Election"
        p = ElectionProfile(testdir + '/blt/' + blt)
        E = Election(p, options)
        E.count()
        return E

    def testElectionCount5(self):
        "try prf-meek-basic default"
        E = self.doCount(dict(rule='prf-meek-basic'), '42.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testElectionCount6(self):
        "prf-meek-basic stable state"
        E = self.doCount(dict(rule='prf-meek-basic', precision=7, omega=7), 'M135.blt')
        self.assertEqual(len(E.elected), E.nSeats)

    def testNickReport(self):
        "using nicknames shouldn't alter dump or report"
        b1 = '''3 2 4 1 2 0 2 3 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        b2 = '''3 2 [nick a b c] 4 a b 0 2 c 0 0 "Castor" "Pollux" "Helen" "Pollux and Helen should tie"'''
        E = Election(ElectionProfile(data=b1), dict(rule='prf-meek-basic'))
        E.count()
        r1 = E.report()
        d1 = E.dump()
        E = Election(ElectionProfile(data=b2), dict(rule='prf-meek-basic'))
        E.count()
        r2 = E.report()
        d2 = E.dump()
        self.assertEqual(r1, r2)
        self.assertEqual(d1, d2)

class ElectionDumpTest(unittest.TestCase):
    "compare some dumps"

    def getDump(self, options, base):
        "run a count and return the dump"
        blt = '%s/blt/%s.blt' % (testdir, base)
        E = Election(ElectionProfile(blt), options)
        E.count()
        return E.dump()

    def testElectionDumpMPRFStable(self):
        "prf-meek-basic stable state"
        self.assertTrue(doDumpCompare(dict(rule='prf-meek-basic', precision=7, omega=7), 'SC-Vm-12'), 'meek-prf stable state')

if __name__ == '__main__':
    unittest.main()
