package defaulted_methods_md;

public class pkg_A_bar_Method extends reflect.Method implements io.datawire.quark.runtime.QObject {
    public pkg_A_bar_Method() {
        super("void", "bar", new java.util.ArrayList(java.util.Arrays.asList(new Object[]{})));
    }
    public Object invoke(Object object, java.util.ArrayList<Object> args) {
        pkg.A obj = (pkg.A) (object);
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
