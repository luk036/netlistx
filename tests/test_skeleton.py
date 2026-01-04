from typing import Any

import pytest

from netlistx.skeleton import fib, main

__author__ = "Wai-Shing Luk"
__copyright__ = "Wai-Shing Luk"
__license__ = "MIT"


def test_fib() -> None:
    """API Tests"""
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(7) == 13
    with pytest.raises(AssertionError):
        fib(-10)


def test_main(capsys: Any) -> None:
    """CLI Tests"""
    # capsys is a pytest fixture that allows asserts agains stdout/stderr
    # https://docs.pytest.org/en/stable/capture.html
    main(["7"])
    captured = capsys.readouterr()
    assert "The 7-th Fibonacci number is 13" in captured.out


def test_main_as_script() -> None:
    """Test running the module as a script to cover the __name__ == '__main__' guard."""
    import subprocess
    import sys

    # Run the skeleton module as a script
    result = subprocess.run(
        [sys.executable, "-m", "netlistx.skeleton", "7"], capture_output=True, text=True
    )

    # Check that the command executed successfully
    assert result.returncode == 0
    # Check the output
    assert "The 7-th Fibonacci number is 13" in result.stdout
