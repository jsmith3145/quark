from contextlib import contextmanager
from collections import deque
from textwrap import dedent

from .match import match, many, lazy


class _Indent(object):
    def __init__(self):
        self.indent = 0

    @contextmanager
    def __call__(self):
        self.indent += 1
        yield " " * self.indent * 2
        self.indent -= 1

_INDENT = _Indent()

class multiline(str):
    """ A string that reprs as a triple-quoted multiline python string """
    def __repr__(self):
        parts = dedent(self).split("\n")
        if len(parts) == 1:
            return repr(parts[0])
        if parts[0]:
            ret = ["'''\\"]
        else:
            ret = ["'''"]
            parts = parts[1:]
        with _INDENT() as indent:
            for part in parts:
                r = repr('\'"' + part) # force ' repr
                assert r.startswith('\'\\\'"'), "String repr hack assumptions are wrong"
                q = r[4:-1] # drop fluff
                ret.append(indent + q)
            ret[-1] += "'''"
            return "\n".join(ret)


def pretty(node, args, kwargs, annotations):
    with _INDENT() as indent:
        if annotations:
            prefix = repr(annotations[0])
            sargs = [pretty(node, args, kwargs, annotations[1:])]
        else:
            prefix = node.__class__.__name__
            sargs = [repr(a) for a in args]
            sargs += ["%s=%r" % (k, v) for k, v in kwargs.items() if v is not None]
        if sum(map(len, sargs)) + len(prefix) > 80:
            first = "\n" + indent
            sep = ",\n" + indent
        else:
            first = ""
            sep = ", "
        return "%s(%s%s)" % (prefix, first, sep.join(sargs))

# should pull in stuff from types base class here... would enable
# comparisons and stuff for testing, should possibly use pyrsistent or
# something like that for this stuff, although I want to see how
# pattern matching would work

class representable(object):
    @match()
    def __init__(self):
        assert False, "%s is abstract base class" % self.__class__

    @match(lazy("representable"))
    def __ne__(self, other):
        return not self.__eq__(other)

    __hash__ = None

    def __repr__(self):
        assert False, "%s does not implement a proper __repr__. Consider delegating to self.repr()" % self.__class__

class _Tree(representable):

    annotations = ()

    @property
    def children(self):
        assert False, "%s must implement children" % self.__class__

    def repr(self, *args, **kwargs):
        return pretty(self, args, kwargs, self.annotations)

class annotation(representable):
    @match(_Tree)
    def __call__(self, node):
        node.annotations = (self, ) + node.annotations
        return node

    def repr(self, *args, **kwargs):
        return pretty(self, args, kwargs, ())


@match(many(type))
def isa(*types):
    """ Generate a predicate for the specifed types """
    return lambda x: isinstance(x, types)


def split(coll, *pred):
    """split coll into tuples that match pred[0] to pred[-1] and one extra
       for all the rest.unless the last predicate is None
    """
    assert pred, "Need at least one predicate"
    if pred[-1] is not None:
        pred = pred + (lambda x: True,)
    else:
        pred = pred[:-1]
    ret = tuple([] for p in pred)
    for el in coll:
        for i,p in enumerate(pred):
            if p(el):
                ret[i].append(el)
                break
        else:
            assert False, "element does not match any of the predicates and wildcard not allowed"
    return tuple(map(tuple,ret))

class Query(object):
    @match(_Tree)
    def __init__(self, tree):
        self.parent_memory = {}
        self.parent_memory[id(tree)] = None
        pending = deque([tree])
        while pending:
            node = pending.popleft()
            for c in node.children:
                assert isinstance(c, _Tree), repr(c)
                self.parent_memory[id(c)] = node
                pending.append(c)

    @match(_Tree)
    def parent(self, node):
        assert id(node) in self.parent_memory
        return self._parent(node)

    @match(_Tree)
    def _parent(self, node):
        return self.parent_memory.get(id(node))

    @match(_Tree)
    def ancestors(self, node):
        parent = self.parent(node)
        while parent is not None:
            yield parent
            parent = self._parent(parent)

    @match(_Tree, (many(type, min=1),))
    def ancestors(self, node, types, ):
        parent = self.parent(node)
        while parent is not None:
            if isinstance(parent, types):
                yield parent
            parent = self._parent(parent)

    @match(_Tree, (many(type, min=1),))
    def ancestors_or_self(self, node, types):
        parent = node
        while parent is not None:
            if isinstance(parent, types):
                yield parent
            parent = self._parent(parent)

    @match(_Tree, (many(type, min=1),))
    def ancestor(self, node, types):
        for ancestor in self.ancestors(node, types):
            return ancestor
        assert False, "No ancestor of type (%s) for node %r" % (", ".join(t.__name__ for t in types), node)

def walk_dfs(tree):
    pending = deque([tree])
    while pending:
        node = pending.popleft()
        yield node
        pending.extendleft(reversed(list(node.children)))

def walk_bfs(tree):
    pending = deque([tree])
    while pending:
        node = pending.popleft()
        yield node
        pending.extend(node.children)

