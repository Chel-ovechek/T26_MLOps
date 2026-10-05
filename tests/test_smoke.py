from mlops_team1 import __version__, ping


def test_package_imports():
    assert __version__ == "0.1.0"


def test_ping():
    assert ping() == "pong"
