from quark_runtime import *

import reflect


class List_reflect_Class_(reflect.Class):
    def _init(self):
        reflect.Class._init(self)

    def __init__(self):
        super(List_reflect_Class_, self).__init__(u"List<reflect.Class>");
        (self).name = u"List"
        (self).parameters = _List([u"reflect.Class"])
        (self).fields = _List([])
        (self).methods = _List([])

    def construct(self, args):
        return _List()

    def _getClass(self):
        return None

    def _getField(self, name):
        return None

    def _setField(self, name, value):
        pass
List_reflect_Class_.singleton = List_reflect_Class_()

class List_reflect_Method_(reflect.Class):
    def _init(self):
        reflect.Class._init(self)

    def __init__(self):
        super(List_reflect_Method_, self).__init__(u"List<reflect.Method>");
        (self).name = u"List"
        (self).parameters = _List([u"reflect.Method"])
        (self).fields = _List([])
        (self).methods = _List([])

    def construct(self, args):
        return _List()

    def _getClass(self):
        return None

    def _getField(self, name):
        return None

    def _setField(self, name, value):
        pass
List_reflect_Method_.singleton = List_reflect_Method_()

class Map_String_reflect_Class_(reflect.Class):
    def _init(self):
        reflect.Class._init(self)

    def __init__(self):
        super(Map_String_reflect_Class_, self).__init__(u"Map<String,reflect.Class>");
        (self).name = u"Map"
        (self).parameters = _List([u"String", u"reflect.Class"])
        (self).fields = _List([])
        (self).methods = _List([])

    def construct(self, args):
        return _Map()

    def _getClass(self):
        return None

    def _getField(self, name):
        return None

    def _setField(self, name, value):
        pass
Map_String_reflect_Class_.singleton = Map_String_reflect_Class_()

class reflect_Class(reflect.Class):
    def _init(self):
        reflect.Class._init(self)

    def __init__(self):
        super(reflect_Class, self).__init__(u"reflect.Class");
        (self).name = u"Class"
        (self).parameters = _List([])
        (self).fields = _List([reflect.Field(u"Map<String,reflect.Class>", u"classes"), reflect.Field(u"reflect.Class", u"VOID"), reflect.Field(u"reflect.Class", u"BOOL"), reflect.Field(u"reflect.Class", u"INT"), reflect.Field(u"reflect.Class", u"LONG"), reflect.Field(u"reflect.Class", u"STRING"), reflect.Field(u"String", u"id"), reflect.Field(u"String", u"name"), reflect.Field(u"List<reflect.Class>", u"parameters"), reflect.Field(u"List<reflect.Field>", u"fields"), reflect.Field(u"List<reflect.Method>", u"methods")])
        (self).methods = _List([])

    def construct(self, args):
        return reflect.Class((args)[0])

    def _getClass(self):
        return None

    def _getField(self, name):
        return None

    def _setField(self, name, value):
        pass
reflect_Class.singleton = reflect_Class()

class reflect_Field(reflect.Class):
    def _init(self):
        reflect.Class._init(self)

    def __init__(self):
        super(reflect_Field, self).__init__(u"reflect.Field");
        (self).name = u"Field"
        (self).parameters = _List([])
        (self).fields = _List([reflect.Field(u"String", u"type"), reflect.Field(u"String", u"name")])
        (self).methods = _List([])

    def construct(self, args):
        return reflect.Field((args)[0], (args)[1])

    def _getClass(self):
        return None

    def _getField(self, name):
        return None

    def _setField(self, name, value):
        pass
reflect_Field.singleton = reflect_Field()

class pkg_Bar_go_Method(reflect.Method):
    def _init(self):
        reflect.Method._init(self)

    def __init__(self):
        super(pkg_Bar_go_Method, self).__init__(u"void", u"go", _List([]));

    def invoke(self, object, args):
        obj = object;
        (obj).go();
        return None

    def _getClass(self):
        return None

    def _getField(self, name):
        return None

    def _setField(self, name, value):
        pass

class pkg_Bar(reflect.Class):
    def _init(self):
        reflect.Class._init(self)

    def __init__(self):
        super(pkg_Bar, self).__init__(u"pkg.Bar");
        (self).name = u"Bar"
        (self).parameters = _List([])
        (self).fields = _List([])
        (self).methods = _List([pkg_Bar_go_Method()])

    def construct(self, args):
        return pkg.Bar()

    def _getClass(self):
        return None

    def _getField(self, name):
        return None

    def _setField(self, name, value):
        pass
pkg_Bar.singleton = pkg_Bar()

class pkg_Foo(reflect.Class):
    def _init(self):
        reflect.Class._init(self)

    def __init__(self):
        super(pkg_Foo, self).__init__(u"pkg.Foo");
        (self).name = u"Foo"
        (self).parameters = _List([])
        (self).fields = _List([reflect.Field(u"String", u"name")])
        (self).methods = _List([])

    def construct(self, args):
        return pkg.Foo()

    def _getClass(self):
        return None

    def _getField(self, name):
        return None

    def _setField(self, name, value):
        pass
pkg_Foo.singleton = pkg_Foo()

class Root(object):
    def _init(self):
        pass
    def __init__(self): self._init()

    def _getClass(self):
        return None

    def _getField(self, name):
        return None

    def _setField(self, name, value):
        pass
Root.pkg_Bar_md = pkg_Bar.singleton
Root.pkg_Foo_md = pkg_Foo.singleton

import pkg
