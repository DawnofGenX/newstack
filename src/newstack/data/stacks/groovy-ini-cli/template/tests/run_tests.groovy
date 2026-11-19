import IniReader

def check = { name, ok ->
    if (ok) { println "ok   ${name}" } else { println "FAIL ${name}"; System.exit(1) }
}

def ini = "[app]\nname=demo\ncount=42\nenabled=true\nratio=1.5\nempty=\n[global]\ntitle=hello\n"
def data = IniReader.parse(ini)

check("section exists", data.containsKey("app"))
check("string value", IniReader.get(data, "app.name") == "demo")
check("int value", IniReader.get(data, "app.count") == 42)
check("int type", IniReader.get(data, "app.count") instanceof Integer)
check("bool value", IniReader.get(data, "app.enabled") == true)
check("bool type", IniReader.get(data, "app.enabled") instanceof Boolean)
check("double value", IniReader.get(data, "app.ratio") == 1.5)
check("global get", IniReader.get(data, "global.title") == "hello")
check("single key get", IniReader.get(data, "title") == "hello")
check("empty string", IniReader.get(data, "app.empty") == "")

// error case
def failed = false
try { IniReader.get(data, "app.missing") } catch (IllegalArgumentException e) { failed = true }
check("missing key throws", failed)

println "checks passed"
System.exit(0)
