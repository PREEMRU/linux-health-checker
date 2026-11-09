from types import SimpleNamespace
from unittest.mock import mock_open, patch

import pytest

from health import (
    check_service,
    get_cpu_usage,
    get_disk_usage,
    get_exit_code,
    get_memory_usage,
    get_status,
    main,
    parse_args,
    read_cpu_stats,
)


@pytest.mark.parametrize("usage, expected", [
    (None, "UNKNOWN"),
    (0, "OK"),
    (50, "OK"),
    (79.99, "OK"),
    (80, "WARNING"),
    (89.9, "WARNING"),
    (90, "CRITICAL"),
    (100, "CRITICAL")
])
def test_get_status(usage, expected):
    assert get_status(usage) == expected

@pytest.mark.parametrize("status, expected", [
    ("OK", 0),
    ("WARNING", 1),
    ("CRITICAL", 2),
    ("UNKNOWN", 3)
])
def test_get_exit_code(status, expected):
    assert get_exit_code(status) == expected

@pytest.mark.parametrize("returncode, expected", [
    (0, True),
    (1, False),
    (2, False),
    (3, False)
])
def test_check_service(returncode, expected):
    with patch("health.subprocess.run") as mock_run:

        mock_run.return_value.returncode = returncode
        result = check_service("ssh")

        mock_run.assert_called_once_with(
            ["systemctl", "is-active", "ssh"],
            capture_output=True, text=True, check=False
        )

        assert result is expected
@pytest.mark.parametrize("return_disk, expected", [
    (SimpleNamespace(total=1000, used=400), 40.0),
    (SimpleNamespace(total=2000, used=1500), 75.0),
    (SimpleNamespace(total=0, used=0), None)
])
def test_get_disk_usage(return_disk, expected):
    with patch("health.shutil.disk_usage", return_value=return_disk):
        result = get_disk_usage()

    assert result == expected

@pytest.mark.parametrize("first, second, expected", [
    (
        [100, 0, 0, 700, 0, 0, 0, 0],
        [150, 0, 0, 750, 0, 0, 0, 0],
        50.0
    ),
    (
        [100, 0, 0, 700, 0, 0, 0, 0],
        [100, 0, 0, 700, 0, 0, 0, 0],
        None
    )
])
def test_get_cpu_usage(first, second, expected):
    with (
        patch("health.read_cpu_stats", side_effect=[first, second]) as mock_stats,
        patch("health.time.sleep"),
        ):
        result = get_cpu_usage()

    assert mock_stats.call_count == 2
    assert result == expected

@pytest.mark.parametrize("fake_ram, expected", [
(
    (
        "MemTotal: 10000 kB\n"
        "MemFree: 1000 kB\n"
        "MemAvailable: 4000 kB\n"
    ),
    60,
),
(
    (
        "MemTotal: 10000 kB\n"
        "MemFree: 1000 kB\n"
    ),
    None,
),
])
def test_get_memory_usage(fake_ram, expected):
    with patch("builtins.open", mock_open(read_data=fake_ram)) as mocked_open:
        result = get_memory_usage()

    mocked_open.assert_called_once_with("/proc/meminfo", "r")
    assert result == expected

@pytest.mark.parametrize("fake_cpu, expected", [
    ("cpu  100 20 30 500 10 0 5 0 0 0\n", [100, 20, 30, 500, 10, 0, 5, 0, 0, 0]),
    ("cpu  0 0 0 0 0 0 0 0 0 0\n", [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ("cpu  999999 0 123456 500000 200 0 50 0 0 0\n", [999999, 0, 123456, 500000, 200, 0, 50, 0, 0, 0]),
    ("cpu  10 20 30 40\n", [10, 20, 30, 40]),
    ("cpu     100     200     300     400\n", [100, 200, 300, 400])
])
def test_read_cpu_stats(fake_cpu, expected):
    with patch("builtins.open", mock_open(read_data=fake_cpu)) as mocked_open:
        result = read_cpu_stats()

    mocked_open.assert_called_once_with("/proc/stat", "r")
    assert result == expected

@pytest.mark.parametrize("cpu, ram, disk, ssh, expected", [
    (10, 20, 30, True, 0),
    (85, 20, 30, True, 1),
    (10, 20, 95, True, 2),
    (10, 20, 30, False, 2),
    (None, 20, 30, True, 3),
    (10, 95, 30, True, 2),
])
def test_main(cpu, ram, disk, ssh, expected, capsys):
    with (
        patch("health.get_cpu_usage", return_value=cpu),
        patch("health.get_memory_usage", return_value=ram),
        patch("health.get_disk_usage", return_value=disk),
        patch("health.check_service", return_value=ssh),pytest.raises(SystemExit) as exc
    ):
        main()

    assert exc.value.code == expected

    captured = capsys.readouterr()
    assert "SERVER HEALTH REPORT" in captured.out
    assert f"CPU:    {cpu}% [{get_status(cpu)}]" in captured.out
    assert f"RAM:    {ram}% [{get_status(ram)}]" in captured.out
    assert f"Disk:   {disk}% [{get_status(disk)}]" in captured.out

    ssh_status = "ACTIVE" if ssh else "INACTIVE"
    assert f"SSH:    {ssh_status}" in captured.out  
    
@pytest.mark.parametrize(
    "usage, warning, critical, expected",
    [
        (65, 70, 85, "OK"),
        (75, 70, 85, "WARNING"),
        (90, 70, 85, "CRITICAL"),
        (85, 80, 90, "WARNING")
    ],
)
def test_custom_thresholds(usage, warning, critical, expected):
    assert get_status(usage, warning, critical) == expected

def test_parse_args_defaults():
    with patch("sys.argv", ["health.py"]):
        args = parse_args()

    assert args.warning == 80
    assert args.critical == 90

def test_parse_args_custom():
    with patch("sys.argv", ["health.py", "--warning", "60", "--critical", "80"]):
        args = parse_args()

    assert args.warning == 60
    assert args.critical == 80

def test_parse_args_invalid():
    with patch("sys.argv", [
        "health.py",
        "--warning", "95",
        "--critical", "30"
    ]), pytest.raises(SystemExit) as exc:
        parse_args()

    assert exc.value.code == 2