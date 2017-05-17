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
import operator
"""
Given a directed graph sort the nodes by their dependecy levels. Refer to
"Large-Scale C++ Software Design" by John Lakos to see why doing this is important
for component systems.

Note:
The roots are at level 1 and all the children... at 2,3,4 ... This is reverse
order than John Lakos's conception where the leafs, that are the lowest level and
parents are above them.
"""
# I hate to use globals but how can we get arount it?
debug_dependency = []
debug_dependency_level = []
debug_nesting_level = 0

class Node:
    def __init__(self):
        self.level=0
        self.children=[]
        self.pushing=False

    def add_child_node(self, child):
        # Make sure no duplicate child is present... no twins allowed :)
        # Converting to set and back to list eliminates duplicate kids
        self.children.append(child)
        self.children = list(set(self.children))

    def _push_level_down(self, parent_level=0):
        """During the levelization process of the tree, this function is used
           to move this node and its children a level down."""
        global debug_dependency
        global debug_nesting_level
        if self.pushing:
            # One of my kids or grand kids... is trying to push me down
            # Cyclic depedency, this is not good, raise hell...
            raise ValueError, "Circular Dependency"
        if (self.level <= parent_level):
            self.level = parent_level+1
            # Push down all my kids
            for c in self.children:
                self.pushing=True
                debug_nesting_level += 1
                debug_dependency.append((c,debug_nesting_level))
                c._push_level_down(self.level)
                debug_nesting_level -= 1
                self.pushing=False

    def _normalize_level(self, offset):
        """If I have no kids, put me at ground level 1. Otherwise,
        calculate my position from the given max."""
        if self.children == []:
            self.level = 1
        else:
            self.level = offset - self.level

    def get_level(self):
        return self.level

    def reset_level(self):
        self.level=0


class Tree:
    def __init__(self):
        # The tree contains a dictionary that key=name and value=instance of
        # node.
        self.node_dict={}
        self.levelized=False

    def add_edge(self, edge):
        # Expecting a tuple (p, c) parent --> child
        if not type(edge) == type(()):
            raise TypeError, edge
        p,c = edge
        # if we don't already have nodes in our dictionary, create them
        if not self.node_dict.has_key(p):
            self.node_dict[p]= Node()
        if not self.node_dict.has_key(c):
            self.node_dict[c]= Node()
        # Now we can create the parent - kid relationship
        if not isinstance(self.node_dict[p], Node):
            raise TypeError, self.node_dict[p]
        self.node_dict[p].add_child_node(self.node_dict[c])

    def delevelize(self):
       for n in self.node_dict.values():
            n.reset_level()


    def levelize(self):
        # Assumptions: All the edges have been added on the tree.
        #              Levelization can only happen once, unless delevelized
        global debug_dependency
        global debug_nesting_level
        if self.levelized:
            raise ValueError, self.levelized
        for n in self.node_dict.values():
            try:
                debug_nesting_level = 0
                debug_dependecy = []
                debug_dependecy.append((n,debug_nesting_level))
                n._push_level_down()
            except ValueError:
                print "Circular dependecy in the source code tree."
                def get_key(dictionary, val):
                    return [k for k, v in dictionary.iteritems() if v == val][0]
                for d in debug_dependency:
                    print "%s[%s]%s" % \
                                (d[1]*'   ', d[1], get_key(self.node_dict, d[0]))
                exit(-1)
        self._normalize_level()
        self.levelized=True

    def max_level(self):
        node_level=[]
        for n in self.node_dict.values():
            node_level.append(n.get_level())
        if node_level:
            return max(node_level)
        else:
            return 0

    def _normalize_level(self):
        """Make the leaf nodes start at 1 and parent nodes in increasing
        order. """
        level_offset = self.max_level()+1
        for n in self.node_dict.values():
            n._normalize_level(level_offset)

    def get_level(self):
        node_level=[]
        for k in self.node_dict.keys():
            node_level.append((k, self.node_dict[k].get_level()))
        return dict(sorted(node_level, key=operator.itemgetter(1)))
