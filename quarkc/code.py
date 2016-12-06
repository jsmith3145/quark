from .match import match, choice, many, ntuple
from .ast import (
    Interface, Class, Function, AST, Package, Primitive, Method, Field, If, Block, Type, Param, While, Switch, Case,
    Local, Call, Attr, Expression, Var, Number, String, Return, Declaration, Assign, ExprStmt, Bool, List, Map, Null,
    Break, Continue, NativeFunction, NativeBlock, Fixed, TypeParam
)
from .symbols import Symbols, name, Self, Boxed, Nulled
from .exceptions import CompileError

import tree

import ir, types, typespace

class View(object):

    def __init__(self, prototypes, bindings):
        self.prototypes = prototypes
        self.bindings = bindings
        self.conversions = self.prototypes.conversions

    def __getitem__(self, node):
        ref = self.prototypes[node]
        tnode = self.prototypes.node(ref)
        return self.bind(ref, tnode)

    @match(types.Ref, typespace.Template)
    def bind(self, ref, tnode):
        ref = types.Ref(ref.name, *(types.Ref(p.name) for p in tnode.params))
        return ref.bind(self.bindings)

    @match(types.Ref, typespace.Type)
    def bind(self, ref, _):
        return ref.bind(self.bindings)

    @match(types.Ref)
    def node(self, ref):
        return self.prototypes.node(ref)

    @match(AST)
    def node(self, node):
        return self.node(self[node])

class Code(object):

    @match(Symbols, types.Types, basestring)
    def __init__(self, symbols, types, package_name):
        self.symbols = symbols
        self.prototypes = types
        self.package_name = package_name

        # Generic types are implemented as templates. This means we
        # run code generation for every unique instantiation of a
        # generic type. The types field holds a view into typespace
        # for each of these unique instantiations.
        self.types = None

        self.asserts = 0
        self.counter = 0
        self.stack = []

    @match(choice(Class))
    def is_top(self, dfn):
        return True

    @match(choice(NativeFunction, Function))
    def is_top(self, fun):
        return True if fun.body else False

    @match(Method)
    def is_top(self, meth):
        return meth.type != None if meth.body and isinstance(meth.parent, Primitive) else False

    @match(choice(AST, [Package], Primitive))
    def is_top(self, dfn):
        return False

    @match()
    def compile(self):
        definitions = []
        for sym, nd in self.symbols.definitions.items():
            if not self.is_top(nd): continue

            for ref, bindings in self.prototypes.instantiations(nd.parent if isinstance(nd, Method) else nd):
                self.types = View(self.prototypes, bindings)
                definitions.append(self.compile(nd))
        # XXX
        return ir.Package(*definitions)

    @match(choice(Function, NativeFunction))
    def compile(self, fun):
        self.asserts = 0
        t = self.types[fun.type]

        if isinstance(fun, NativeFunction):
            sym = name(fun).split("::")[1]
        else:
            sym = name(fun)

        args = [self.compile_def(sym), self.compile(t)] + self.compile(fun.params)
        if isinstance(fun, NativeFunction):
            args += self.compile(fun.body)
        else:
            args += [self.compile(fun.body)]

        if self.asserts:
            return ir.Check(args[0], *args[2:])
        else:
            if isinstance(fun, NativeFunction):
                return ir.NativeFunction(*args)
            else:
                return ir.Function(*args)

    @match(NativeBlock)
    def compile(self, block):
        mappings = []

        for c in block.children:
            if isinstance(c, Var):
                mappings.append((c.name.text, self.compile(c)))
        return [ir.TemplateContext(*mappings),
                ir.TemplateText(block.target, tuple(ir.NativeImport(self.unquote(m), a) for m, a in block.imports),
                                "".join(self.compile_native(c) for c in block.children))]

    @match(Fixed)
    def compile_native(self, fixed):
        return fixed.text.replace("{","{{").replace("}","}}")

    @match(Var)
    def compile_native(self, var):
        return "{%s}" % var.name.text

    @match(Class)
    def compile(self, cls):
        self.asserts = 0
        args = tuple([self.compile_def(self.mangle(self.types[cls]))]
                     + [self.compile(d) for d in cls.bases + cls.definitions])
        if self.asserts:
            klazz = ir.TestClass
            constructors, args = tree.split(args, tree.isa(ir.Constructor))
            if constructors:
                # XXX: how to not warn for autogenerated constructors (by frontend)
                print("XXX: TODO compile error, class %s is a test class, cannot have a constructor" % args[0])
        else:
            klazz = ir.Class
        return klazz(*args)

    @match(Field)
    def compile(self, field):
        return ir.Field(field.name.text, self.compile(self.types[field]))

    @match(Method)
    def compile(self, meth):
        if isinstance(meth.parent, Primitive):
            if isinstance(meth.body, NativeBlock):
                klass = ir.NativeFunction
            else:
                klass = ir.Function
            nam = self.compile_def(self.mangle(self.types[meth.parent]) + "_" + meth.name.text)
            ret = self.types.node(meth).result
            if meth.name.text == "__init__":
                extra = []
            else:
                extra = [ir.Param("self", self.compile(self.types[meth.parent]))]
        elif meth.type:
            klass = ir.Method
            nam = meth.name.text
            ret = self.types[meth.type]
            extra = []
        else:
            klass = ir.Constructor
            nam = self.mangle(meth.name.text, *self.types[meth.parent].params)
            ret = self.types.node(meth).result
            extra = []

        old_asserts = self.asserts # don't reset asserts because Class checks for asserts, too
        args = [nam, self.compile(ret)] + extra + self.compile(meth.params)
        if isinstance(meth.body, NativeBlock):
            args.extend(self.compile(meth.body))
        else:
            args += [self.compile(meth.body)]
        if self.asserts != old_asserts:
            klass = ir.TestMethod

        return klass(*args)

    @match(Interface)
    def compile(self, iface):
        return ir.Interface(self.compile_def(self.mangle(self.types[iface])),
                            *[self.compile_interface(d) for d in iface.definitions])

    @match(Method)
    def compile_interface(self, meth):
        assert meth.type
        assert not meth.body
        return ir.Message(meth.name.text, self.compile(self.types.node(meth).result), *self.compile(meth.params))

    @match(types.Ref)
    def compile_ref(self, ref):
        return self.compile_ref(ref, "")

    @match(types.Ref, basestring)
    def compile_ref(self, ref, suffix):
        return self.compile_ref(self.mangle(ref) + suffix)

    @match(types.Ref)
    def mangle(self, ref):
        return self.mangle(ref.name, *ref.params)

    @match(basestring, many(types.Ref))
    def mangle(self, name, *params):
        return "_".join([name] + [self.mangle_param(p).replace(".", "_") for p in params])

    @match(types.Ref)
    def mangle_param(self, ref):
        return "_".join([self.mangle_param(ref.name)] +
                        [self.mangle_param(p).replace(".", "_") for p in ref.params])

    @match("quark.int")
    def mangle_param(self, sym):
        return "int"

    @match("quark.String")
    def mangle_param(self, sym):
        return "String"

    @match("quark.Any")
    def mangle_param(self, sym):
        return "Any"

    @match("quark.Scalar")
    def mangle_param(self, sym):
        return "Scalar"

    @match("quark.List")
    def mangle_param(self, sym):
        return "List"

    @match("quark.Map")
    def mangle_param(self, sym):
        return "Map"

    @match(basestring)
    def mangle_param(self, sym):
        return sym

    @match(basestring)
    def compile_ref(self, name):
        return ir.Ref("{}:{}".format(self.package_name, self.package_name), name)

    @match(basestring)
    def compile_def(self, name):
        return ir.Name("{}:{}".format(self.package_name, self.package_name), name)

    @match(types.Ref("quark.int"))
    def compile(self, ref):
        return ir.Int()

    @match(types.Ref("quark.float"))
    def compile(self, ref):
        return ir.Float()

    @match(types.Ref("quark.Any"))
    def compile(self, ref):
        return ir.Any()

    @match(types.Ref("quark.Scalar"))
    def compile(self, ref):
        return ir.Scalar()

    @match(types.Ref("quark.bool"))
    def compile(self, ref):
        return ir.Bool()

    @match(types.Ref("quark.String"))
    def compile(self, ref):
        return ir.String()

    @match(types.Ref("quark.void"))
    def compile(self, ref):
        return ir.Void()

    @match(types.Ref)
    def compile(self, ref):
        return self.compile(ref.name, *ref.params)

    @match(basestring, many(types.Ref))
    def compile(self, nam, *params):
        dfn = self.symbols[nam]
        if isinstance(dfn, Interface):
            return ir.InterfaceType(self.compile_ref(self.mangle(nam, *params)))
        elif isinstance(dfn, Primitive):
            # XXX
            bindings = {}
            for p, v in zip(dfn.parameters, params):
                bindings[name(p)] = v
            old = self.types
            self.types = View(self.prototypes, bindings)
            args = [ir.NativeBlock(*self.compile(m)) for m in dfn.mappings]
            if not args:
                raise CompileError("%s: missing type mappings" % dfn.location)
            result = ir.Primitive(*args)
            self.types = old
            return result
        else:
            return ir.ClassType(self.compile_ref(self.mangle(nam, *params)))

    @match(Type)
    def compile(self, t):
        return self.compile(self.types[t])

    @match(ntuple(Param))
    def compile(self, params):
        return [ir.Param(p.name.text, self.compile(p.type)) for p in params]

    @match(ir.AbstractType)
    def temp(self, type):
        tmp = "temp%s" % self.counter
        self.counter += 1
        self.add(ir.Local(tmp, type))
        return tmp

    @match(ir.Statement)
    def add(self, stmt):
        self.stack[-1].append(stmt)

    def push(self):
        self.stack.append([])

    def pop(self):
        return self.stack.pop()

    @match(Block)
    def compile(self, block):
        stmts = []
        for s in block.statements:
            self.push()
            c = self.compile(s)
            stmts.extend(self.pop())
            stmts.append(c)
        return ir.Block(*stmts)

    @match(If)
    def compile(self, if_):
        alt = self.compile(if_.alternative) if if_.alternative else ir.Block()
        return ir.If(self.compile(if_.predicate), self.compile(if_.consequence), alt)

    @match(While)
    def compile(self, while_):
        return ir.While(self.compile(while_.condition), self.compile(while_.body))

    @match(Switch)
    def compile(self, switch):
        tmp = self.temp(self.compile(self.types[switch.expr]))
        self.add(ir.Assign(ir.Var(tmp), self.compile(switch.expr)))
        return self.compile(self.types[switch.expr], tmp, *switch.cases)

    @match(types.Ref, basestring, many(Case, min=2))
    def compile(self, ref, temp, first, *rest):
        return ir.If(self.compile_case(ref, temp, *first.exprs),
                     self.compile(first.body),
                     ir.Block(self.compile(ref, temp, *rest)))

    @match(types.Ref, basestring, Case)
    def compile(self, ref, temp, case):
        return ir.If(self.compile_case(ref, temp, *case.exprs), self.compile(case.body), ir.Block())

    @match(types.Ref, basestring, many(Expression, min=2))
    def compile_case(self, ref, temp, first, *rest):
        test = self.compile_send(ref, ir.Var(temp), "__eq__", first)
        return self.compile_send(types.Ref("quark.bool"), test, "__or__", self.compile_case(ref, temp, *rest))

    @match(types.Ref, basestring, Expression)
    def compile_case(self, ref, temp, expr):
        return self.compile_send(ref, ir.Var(temp), "__eq__", expr)

    @match(types.Ref, ir.Expression, basestring, many(Expression, min=1))
    def compile_send(self, ref, expr, name, *args):
        return self.compile_send(ref, expr, name, *[self.compile(a) for a in args])

    @match(types.Ref, ir.Expression, basestring, many(ir.Expression))
    def compile_send(self, ref, expr, name, *args):
        mref = self.types.node(ref).byname[name].type
        cls = self.symbols[ref.name]
        meth = self.symbols[mref.name]
        return self.compile_call_method(mref, cls, meth, expr, list(args))

    @match(Local)
    def compile(self, local):
        expr = (self.compile(local.declaration.value),) if local.declaration.value else ()
        return ir.Local(local.declaration.name.text, self.compile(self.types[local]), *expr)

    @match(Call)
    def compile(self, call):
        return self.convert(call, self.compile_call(call.expr, call.args))

    # this needs to be called on the result of compiling all expressions
    @match(Expression, ir.Expression)
    def convert(self, expr, compiled):
        if expr in self.types.conversions:
            return self.compile_send(self.types[expr], compiled, self.types.conversions[expr])
        else:
            return compiled

    @match(Expression, choice(ir.AbstractType, ir.AssertEqual,
                              ir.AssertNotEqual, ir.Ref))
    def convert(self, _, compiled):
        return compiled

    @match(choice(Expression, Type), [many(Expression)])
    def compile_call(self, expr, args):
        t = self.types[expr]
        assert isinstance(t, types.Ref)
        dfn = self.symbols[t.name]
        return self.compile_call(t, dfn, expr, args)

    @match(types.Ref, Method, Attr, [many(Expression)])
    def compile_call(self, ref, dfn, attr, args):
        assert attr.attr.text == dfn.name.text
        return self.compile_call_method(ref, dfn.parent, dfn, self.compile(attr.expr), args)

    @match(types.Ref, Method, Var, [many(Expression)])
    def compile_call(self, ref, dfn, var, args):
        assert var.name.text == dfn.name.text
        return self.compile_call_method(ref, dfn.parent, dfn, ir.This(), args)

    @match(types.Ref, Class, Method, ir.Expression, [many(Expression, min=1)])
    def compile_call_method(self, ref, objdfn, methdfn, expr, args):
        return self.compile_call_method(ref, objdfn, methdfn, expr, [self.compile(a) for a in args])

    @match(types.Ref, Class, Method, ir.Expression, [many(ir.Expression)])
    def compile_call_method(self, ref, objdfn, methdfn, expr, args):
        return ir.Send(expr, methdfn.name.text, tuple(args))

    @match(types.Ref, Primitive, Method, ir.Expression, [many(ir.Expression)])
    def compile_call_method(self, ref, objdfn, methdfn, expr, args):
        return self.compile_call_primitive(ref, objdfn, self.types[objdfn], methdfn, expr, args)

    @match(types.Ref, Primitive, types.Ref, Method, ir.Expression, [many(ir.Expression)])
    def compile_call_primitive(self, ref, objdfn, methref, methdfn, expr, args):
        n = "%s_%s" % (self.mangle(name(objdfn), *ref.params), methdfn.name.text)
        return ir.Invoke(self.compile_ref(n), expr, *args)

    @match(types.Ref, Primitive, types.Ref("quark.bool"), Method, ir.Expression, [many(ir.Expression)])
    def compile_call_primitive(self, ref, objdfn, methref, methdfn, expr, args):
        return self.compile_call_boolop(ref, objdfn, methref, methdfn.name.text, expr, args)

    @match(types.Ref, Primitive, types.Ref("quark.bool"), basestring, ir.Expression, [many(ir.Expression)])
    def compile_call_boolop(self, ref, objdfn, methref, methname, expr, args):
        n = "%s_%s" % (self.mangle(name(objdfn), *ref.params), methname)
        return ir.Invoke(self.compile_ref(n), expr, *args)

    @match(types.Ref, Primitive, types.Ref("quark.bool"), "__or__", ir.Expression, [many(ir.Expression)])
    def compile_call_boolop(self, ref, objdfn, methref, methname, expr, args):
        return ir.Or(expr, *args)

    @match(types.Ref, Primitive, types.Ref("quark.bool"), "__and__", ir.Expression, [many(ir.Expression)])
    def compile_call_boolop(self, ref, objdfn, methref, methname, expr, args):
        return ir.And(expr, *args)

    @match(types.Ref, choice(NativeFunction, Function), Var, [many(Expression)])
    def compile_call(self, ref, dfn, var, args):
        return self.compile_call(ref, dfn, var.name.text, args)

    @match(types.Ref, choice(NativeFunction, Function), basestring, [many(Expression)])
    def compile_call(self, ref, dfn, fun, args):
        return ir.Invoke(self.compile_ref(name(dfn)), *[self.compile(a) for a in args])

    @match(types.Ref, Function, "assertEqual", [many(Expression)])
    def compile_call(self, ref, dfn, fun, args):
        self.asserts += 1
        return ir.AssertEqual(*[self.compile(a) for a in args])

    @match(types.Ref, Function, "assertNotEqual", [many(Expression)])
    def compile_call(self, ref, dfn, fun, args):
        self.asserts += 1
        return ir.AssertNotEqual(*[self.compile(a) for a in args])

    @match(types.Ref, Method, Type, [many(Expression)])
    def compile_call(self, ref, cons, type, args):
        return self.compile_call(ref, cons, args)

    @match(types.Ref, Method, [many(Expression)])
    def compile_call(self, ref, cons, args):
        callable = self.types.node(ref)
        if isinstance(cons.parent, Primitive):
            return ir.Invoke(self.compile_ref(callable.result, "___init__"), *[self.compile(a) for a in args])
        else:
            return ir.Construct(self.compile_ref(callable.result), tuple([self.compile(a) for a in args]))

    @match(Attr)
    def compile(self, attr):
        return self.convert(attr, ir.Get(self.compile(attr.expr), attr.attr.text))

    @match(Number)
    def compile(self, n):
        if n.is_float():
            return self.convert(n, ir.FloatLit(float(n.text)))
        else:
            return self.convert(n, ir.IntLit(int(n.text)))

    @match(String)
    def compile(self, s):
        return self.convert(s, ir.StringLit(self.unquote(s.text)))

    @match(basestring)
    def unquote(self, s):
        value = ""
        idx = 1
        while idx < len(s) - 1:
            c = s[idx]
            next = s[idx + 1]
            if c == "\\":
                if next == "x":
                    value += chr(int(s[idx+2:idx+4], 16))
                    idx += 4
                elif next == "n":
                    value += "\n"
                    idx += 2
                elif next == "r":
                    value += "\r"
                    idx += 2
                elif next == "t":
                    value += "\t"
                    idx += 2
                elif next == '"':
                    value += '"'
                    idx += 2
                elif next == '\\':
                    value += '\\'
                    idx += 2
                else:
                    assert False, "bad string literal: %s" % s
            else:
                value += c
                idx += 1
        return value

    @match(Bool)
    def compile(self, b):
        return self.convert(b, ir.BoolLit(b.text == "true"))

    @match(List)
    def compile(self, l):
        ref = self.types[l]
        tmp = self.temp(self.compile(ref))
        lst = self.symbols[ref.name]
        mref = types.Ref("%s.%s" % (ref.name, lst.name.text), *ref.params)
        self.add(ir.Assign(ir.Var(tmp), self.compile_call(mref, self.symbols[mref.name], [])))
        for el in l.elements:
            self.add(ir.Evaluate(self.compile_send(ref, ir.Var(tmp), "append", el)))
        return self.convert(l, ir.Var(tmp))

    @match(Map)
    def compile(self, m):
        ref = self.types[m]
        tmp = self.temp(self.compile(ref))
        map = self.symbols[ref.name]
        mref = types.Ref("%s.%s" % (ref.name, map.name.text), *ref.params)
        self.add(ir.Assign(ir.Var(tmp), self.compile_call(mref, self.symbols[mref.name], [])))
        for entry in m.entries:
            self.add(ir.Evaluate(self.compile_send(ref, ir.Var(tmp), "__set__", self.compile(entry.key), self.compile(entry.value))))
        return self.convert(m, ir.Var(tmp))

    @match(Null)
    def compile(self, n):
        return self.convert(n, ir.Null(self.compile(self.types[n])))

    @match(Return)
    def compile(self, retr):
        return ir.Return(self.compile(retr.expr))

    @match(Var)
    def compile(self, var):
        return self.convert(var, self.compile_var(self.symbols[var], var))

    @match(choice(Param, Declaration), Var)
    def compile_var(self, p, v):
        return ir.Var(v.name.text)

    @match(Field, Var)
    def compile_var(self, p, v):
        return ir.Get(ir.This(), v.name.text)

    @match(Self, Var)
    def compile_var(self, s, v):
        if isinstance(s.klass, Primitive):
            return ir.Var("self")
        else:
            return ir.This()

    @match(Boxed, Var)
    def compile_var(self, b, v):
        t = self.compile(self.types[b])
        if isinstance(t, ir.NativeType):
            return ir.Boxed(t)
        else:
            return t

    @match(Nulled, Var)
    def compile_var(self, b, v):
        t = self.compile(self.types[b])
        return ir.Null(t)

    @match(TypeParam, Var)
    def compile_var(self, p, v):
        return self.compile(self.types[p])

    @match(Function, Var)
    def compile_var(self, f, v):
        return self.compile_ref(self.types[f])

    @match(Assign)
    def compile(self, ass):
        return self.compile_assign(ass.lhs, ass.rhs)

    @match(Var, Expression)
    def compile_assign(self, var, expr):
        return self.compile_assign(self.symbols[var], var, expr)

    @match(Field, Var, Expression)
    def compile_assign(self, field, var, expr):
        return ir.Set(ir.This(), var.name.text, self.compile(expr))

    @match(choice(Param, Declaration), Var, Expression)
    def compile_assign(self, decl, var, expr):
        return ir.Assign(self.compile(var), self.compile(expr))

    @match(Attr, Expression)
    def compile_assign(self, attr, expr):
        return ir.Set(self.compile(attr.expr), attr.attr.text, self.compile(expr))

    @match(ExprStmt)
    def compile(self, exprs):
        return self.to_stmt(self.compile(exprs.expr))

    @match(ir.Statement)
    def to_stmt(self, stmt):
        return stmt

    @match(ir.Expression)
    def to_stmt(self, expr):
        return ir.Evaluate(expr)

    @match(Break)
    def compile(self, brk):
        return ir.Break()

    @match(Continue)
    def compile(self, brk):
        return ir.Continue()
