package package_md;

public class test_Test extends reflect.Class implements io.datawire.quark.runtime.QObject {
    public static reflect.Class singleton = new test_Test();
    public test_Test() {
        super("test.Test");
        (this).name = "Test";
        (this).parameters = new java.util.ArrayList(java.util.Arrays.asList(new Object[]{}));
        (this).fields = new java.util.ArrayList(java.util.Arrays.asList(new Object[]{new reflect.Field("String", "name")}));
        (this).methods = new java.util.ArrayList(java.util.Arrays.asList(new Object[]{new test_Test_go_Method()}));
    }
    public Object construct(java.util.ArrayList<Object> args) {
        return new test.Test();
    }
    public String _getClass() {
        return (String) (null);
    }
    public Object _getField(String name) {
        return null;
    }
    public void _setField(String name, Object value) {}
}
