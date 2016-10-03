from .match import *
from .errors import *
from .parse import *
from .symbols import *
from .traits import *

import ir, types, typeconstruction, irconstruction

@match(choice(Function, Interface, Class))
def toplevel(dfn):
    return True

@match(choice(AST, [Package], Primitive))
def toplevel(dfn):
    return False

class Compiler(object):

    MATCH_TRAITS = COMPILER

    def __init__(self):
        self.errors = Errors()
        self.symbols = Symbols(self.errors)
        self.types = types.Typespace(self.errors)

    @match(basestring, basestring)
    def parse(self, name, content):
        try:
            file = parse(name, content)
            self.symbols.add(file)
        except ParseError, e:
            self.errors.add(str(e))

    @match()
    def check(self):
        self.errors.check()
        for k, v in self.symbols.definitions.items():
            t = typeconstruction.type(self, v)
            if t is not None:
                self.types[k] = t
        for k, v in self.symbols.definitions.items():
            if not isinstance(v, list):
                traverse(v, lambda x: typeconstruction.check(self, x))
        self.errors.check()

    @match()
    def compile(self):
        dfns = []
        for k, v in self.symbols.definitions.items():
            if toplevel(v):
                iro = irconstruction.compile(self, k, v)
                if iro:
                    dfns.append(iro)
        return ir.Package(*dfns)


if __name__ == "__main__":
    c = Compiler()
    c.parse("fib", """
    namespace quark {
        primitive int {
            int __add__(int other);
            int __sub__(int other);
            int __mul__(int other);
            bool __lt__(int other);
            bool __eq__(int other);
            String toString();
        }

        primitive bool {
            bool __eq__(bool other);
            String toString();
        }

        primitive String {
            bool __lt__(String other);
            bool __eq__(String other);
            String toString();
        }
    }

    namespace math {
        int fib(int n) {
            if (n < 2) {
                return n;
            } else {
                return fib(n-1) + fib(n-2);
            }
        }
    }

    import math;

    namespace other {
        int fib2(int n) {
            return 2*fib(n);
        }
    }
    """)

    c.check()
    pkg = c.compile()
    print pkg
    import emit, sys
    tgt = emit.Ruby()
    emit.emit(pkg, tgt)
    for file in tgt.files.values():
        print "===%s===" % file.name
        sys.stdout.write(str(file))