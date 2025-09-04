from persishell import PersiShell

def test_env():
    sh = PersiShell()
    errorcode = sh.export("TESTVAR", "VALUE")
    assert errorcode == 0
    ret = sh.run("echo $TESTVAR")
    assert ret.stdout.strip() == "VALUE"
    errorcode = sh.unset("TESTVAR")
    assert errorcode == 0
    ret = sh.run("echo $TESTVAR")
    assert ret.stdout.strip() == ""