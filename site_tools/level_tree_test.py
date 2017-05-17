#-------------------------------------------------------------------------------
# Copyright (C) 05/2017 Eyob Demissie
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THETHE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# Except as contained in this notice, the name(s) of the above copyright holders 
# shall not be used in advertising or otherwise to promote the sale, use or other
# dealings in this Software without prior written authorization.
#-------------------------------------------------------------------------------
import level_tree
import unittest


class TestLeveling(unittest.TestCase):
    def testSimpleTree(self):
        #  [4]     [3]     [2]     [1]
        # t_1a ----------> t_3 --> t_4
        # t_1b --> t_2------^
        lt_eg = [('t_1a','t_3'), ('t_1b','t_2'), ('t_3','t_4'), ('t_2','t_3')]
        lt_levels_expected = {'t_1a':4, 't_1b':4, 't_2':3, 't_3':2, 't_4':1}
        lt = level_tree.Tree()
        for e in lt_eg:
            lt.add_edge(e)
        lt.levelize()
        lt_levels_result = lt.get_level()
        for k in lt_levels_result.keys():
            self.assertEqual(lt_levels_expected[k], lt_levels_result[k])

    def testRepeatedEdge(self):
        #  [4]     [3]     [2]     [1]
        # t_1a ----------> t_3 --> t_4
        # t_1b --> t_2------^
        lt_eg = [('t_1a','t_3'), ('t_1b','t_2'), ('t_3','t_4'),
                 ('t_2','t_3'), ('t_2','t_3')]
        lt_levels_expected = {'t_1a':4, 't_1b':4, 't_2':3, 't_3':2, 't_4':1}
        lt = level_tree.Tree()
        for e in lt_eg:
            lt.add_edge(e)
        lt.levelize()
        lt_levels_result = lt.get_level()
        for k in lt_levels_result.keys():
            self.assertEqual(lt_levels_expected[k], lt_levels_result[k])


class TestWeirdInput(unittest.TestCase):
    def testLevelizeMoreThanOnce(self):
        lt_eg = [('t_1a','t_3'), ('t_1b','t_2'), ('t_3','t_4'), ('t_2','t_3')]
        lt = level_tree.Tree()
        for e in lt_eg:
            lt.add_edge(e)
        lt.levelize()
        self.assertRaises(ValueError, lt.levelize)

    def testNonTupleEdge(self):
        lt = level_tree.Tree()
        self.assertRaises(TypeError, lt.add_edge, 1)
        self.assertRaises(TypeError, lt.add_edge, [('a','b')])
        self.assertRaises(TypeError, lt.add_edge, {})


if __name__ == '__main__':
    unittest.main()
