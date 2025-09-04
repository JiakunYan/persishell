from persishell import PersiShell

def test_env():
    sh = PersiShell()
    errorcode = sh.export("TESTVAR", "VALUE")
    assert errorcode == 0
    errorcode, stdout, stderr = sh.run("echo $TESTVAR")
    assert stdout.strip() == "VALUE"
    errorcode = sh.unset("TESTVAR")
    assert errorcode == 0
    errorcode, stdout, stderr = sh.run("echo $TESTVAR")
    assert stdout.strip() == ""