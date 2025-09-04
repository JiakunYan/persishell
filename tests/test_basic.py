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

def test_print_wo_newline():
    sh = PersiShell()
    ret = sh.run("printf 'hello'; printf 'world'")
    assert ret.returncode == 0
    assert ret.stdout.strip() == "helloworld"

def test_error():
    sh = PersiShell()
    ret = sh.run("ls non_existent_file")
    assert ret.returncode != 0
    assert "No such file or directory" in ret.stderr