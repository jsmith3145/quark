package defaulted_methods_md;

public class pkg_B_bar_Method extends reflect.Method implements io.datawire.quark.runtime.QObject {
    public pkg_B_bar_Method() {
        super("builtin.void", "bar", new java.util.ArrayList(java.util.Arrays.asList(new Object[]{})));
    }
    public Object invoke(Object object, java.util.ArrayList<Object> args) {
        pkg.B obj = (pkg.B) (object);
        (obj).bar();
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