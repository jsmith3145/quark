public class Functions {
    public static void test_roundtrip() {
        System.out.println((io.datawire.quark_runtime.JSONObject.parse(((new io.datawire.quark_runtime.JSONObject()).setObject()).toString())).toString());
        System.out.println((io.datawire.quark_runtime.JSONObject.parse(((new io.datawire.quark_runtime.JSONObject()).setList()).toString())).toString());
        System.out.println((io.datawire.quark_runtime.JSONObject.parse(((new io.datawire.quark_runtime.JSONObject()).setString("")).toString())).toString());
        System.out.println((io.datawire.quark_runtime.JSONObject.parse(((new io.datawire.quark_runtime.JSONObject()).setBool(false)).toString())).toString());
        System.out.println((io.datawire.quark_runtime.JSONObject.parse(((new io.datawire.quark_runtime.JSONObject()).setBool(true)).toString())).toString());
        System.out.println((io.datawire.quark_runtime.JSONObject.parse(((new io.datawire.quark_runtime.JSONObject()).setNull()).toString())).toString());
    }
    public static void test_iterate_list() {
        io.datawire.quark_runtime.JSONObject l = io.datawire.quark_runtime.JSONObject.parse("[1.2,2.3,3.4,4.5,5.6,6.7,7.8]");
        Integer i = 0;
        io.datawire.quark_runtime.JSONObject item = (l).getListItem(i);
        while (!((item).equals((l).undefined()))) {
            System.out.println(((("l[") + (Integer.toString(i))) + ("] = ")) + (Double.toString((item).getNumber())));
            i = (i) + (1);
            item = (l).getListItem(i);
            if ((i) > (10)) {
                System.out.println("Error!");
                return;
            }
        }
    }
    public static void test_iterate_list_directory() {
        String message = ((new io.datawire.quark_runtime.JSONObject()).setObjectItem("endpoints", (((new io.datawire.quark_runtime.JSONObject()).setListItem(0, (new io.datawire.quark_runtime.JSONObject()).setString("endpoint0"))).setListItem(1, (new io.datawire.quark_runtime.JSONObject()).setString("endpoint1"))).setListItem(2, (new io.datawire.quark_runtime.JSONObject()).setString("endpoint2")))).toString();
        System.out.println(message);
        io.datawire.quark_runtime.JSONObject jobj = io.datawire.quark_runtime.JSONObject.parse(message);
        io.datawire.quark_runtime.JSONObject endpoints = (jobj).getObjectItem("endpoints");
        Integer i = 0;
        io.datawire.quark_runtime.JSONObject endpoint = (endpoints).getListItem(i);
        while (!((endpoint).equals((endpoints).undefined()))) {
            String ep = (endpoint).getString();
            System.out.println(ep);
            i = (i) + (1);
            endpoint = (endpoints).getListItem(i);
        }
    }
    public static void main() {
        Functions.test_roundtrip();
        Functions.test_iterate_list();
        Functions.test_iterate_list_directory();
    }
    public static void main(String[] args) {
        main();
    }
}