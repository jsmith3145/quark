package defaulted_methods_md;

public class pkg_T5_foo_Method extends reflect.Method implements io.datawire.quark.runtime.QObject {
    public pkg_T5_foo_Method() {
        super("void", "foo", new java.util.ArrayList(java.util.Arrays.asList(new Object[]{})));
    }
    public Object invoke(Object object, java.util.ArrayList<Object> args) {
        pkg.T5 obj = (pkg.T5) (object);
        (obj).foo();
        return null;
    }
    public String _getClass() {
        return (String) (null);
    }
    public Object _getField(String name) {
        return null;
    }
    public void _setField(String name, Object value) {}
}
