import asyncio
import pytest
from services.sandbox.models import SandboxStatus
from services.sandbox.service import SandboxService


@pytest.fixture
def sandbox():
    return SandboxService(mode="isolated")  # Use isolated mode for fast reproducible unit test suite


# ---------------------------------------------------------
# 1. Valid Python Execution & Test Suite Verification
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_sandbox_valid_code_execution(sandbox):
    code = (
        "def pump_head_loss(flow, length, diameter, friction=0.02):\n"
        "    v = (flow / 3600) / (3.14159 * (diameter / 2)**2)\n"
        "    h_loss = friction * (length / diameter) * (v**2 / (2 * 9.81))\n"
        "    return round(h_loss, 3)\n\n"
        "res = pump_head_loss(150, 200, 0.15)\n"
        "print(f'HEAD_LOSS_METERS:{res}')\n"
    )
    result = await sandbox.execute_python(code=code)
    assert result.status == SandboxStatus.SUCCESS.value
    assert result.exit_code == 0
    assert "HEAD_LOSS_METERS:" in result.stdout
    assert result.cleanup_verified is True
    assert result.duration_ms > 0


@pytest.mark.asyncio
async def test_sandbox_with_pytest_suite(sandbox):
    main_code = (
        "def calculate_pump_efficiency(flow_m3h, head_m, power_kw, density=850):\n"
        "    q_m3s = flow_m3h / 3600.0\n"
        "    hyd_power = (density * 9.81 * q_m3s * head_m) / 1000.0\n"
        "    eff = hyd_power / power_kw\n"
        "    return round(eff, 4)\n"
    )
    test_files = {
        "test_efficiency.py": (
            "from main import calculate_pump_efficiency\n\n"
            "def test_normal_operating_efficiency():\n"
            "    eff = calculate_pump_efficiency(150, 45, 22.0)\n"
            "    assert eff > 0.60\n"
            "    assert eff < 0.90\n\n"
            "def test_zero_flow_efficiency():\n"
            "    eff = calculate_pump_efficiency(0, 45, 22.0)\n"
            "    assert eff == 0.0\n"
        )
    }
    result = await sandbox.execute_python(code=main_code, test_files=test_files)
    assert result.status == SandboxStatus.SUCCESS.value
    assert result.exit_code == 0
    assert len(result.tests) >= 2
    for t in result.tests:
        assert t.status == "passed"


# ---------------------------------------------------------
# 2. Security Test: Infinite Loops & Timeouts
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_sandbox_infinite_loop_timeout(sandbox):
    infinite_loop_code = (
        "import time\n"
        "while True:\n"
        "    time.sleep(0.1)\n"
    )
    # Fast 1-second timeout for test
    result = await sandbox.execute_python(code=infinite_loop_code, timeout_seconds=1)
    assert result.status == SandboxStatus.TIMEOUT.value
    assert result.exit_code == -1
    assert "timed out" in result.stderr.lower()


# ---------------------------------------------------------
# 3. Security Test: Host Filesystem Access Attempts
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_sandbox_blocks_host_filesystem_access(sandbox):
    # Attempt 1: Linux shadow / passwd
    malicious_code_1 = "f = open('/etc/shadow', 'r')\nprint(f.read())"
    res1 = await sandbox.execute_python(code=malicious_code_1)
    assert res1.status == SandboxStatus.SECURITY_BLOCKED.value
    assert "filesystem access" in res1.stderr.lower()

    # Attempt 2: Windows System32
    malicious_code_2 = "import os\nos.listdir('C:\\\\Windows\\\\System32')"
    res2 = await sandbox.execute_python(code=malicious_code_2)
    assert res2.status == SandboxStatus.SECURITY_BLOCKED.value

    # Attempt 3: Secret .env traversal
    malicious_code_3 = "f = open('../../.env', 'r')\nprint(f.read())"
    res3 = await sandbox.execute_python(code=malicious_code_3)
    assert res3.status == SandboxStatus.SECURITY_BLOCKED.value


# ---------------------------------------------------------
# 4. Security Test: Outbound Network Access Attempts
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_sandbox_blocks_network_access(sandbox):
    # Attempt 1: Raw socket connect
    socket_code = (
        "import socket\n"
        "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
        "s.connect(('8.8.8.8', 53))\n"
    )
    res1 = await sandbox.execute_python(code=socket_code)
    assert res1.status == SandboxStatus.SECURITY_BLOCKED.value
    assert "network" in res1.stderr.lower()

    # Attempt 2: HTTP requests
    http_code = "import urllib.request\nurllib.request.urlopen('http://google.com')"
    res2 = await sandbox.execute_python(code=http_code)
    assert res2.status == SandboxStatus.SECURITY_BLOCKED.value


# ---------------------------------------------------------
# 5. Security Test: Subprocess & Shell Escalation Attempts
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_sandbox_blocks_subprocess_escalation(sandbox):
    # Attempt 1: Subprocess module
    subprocess_code = "import subprocess\nsubprocess.Popen(['ls', '-la'])"
    res1 = await sandbox.execute_python(code=subprocess_code)
    assert res1.status == SandboxStatus.SECURITY_BLOCKED.value
    assert "subprocess" in res1.stderr.lower()

    # Attempt 2: os.system
    os_sys_code = "import os\nos.system('whoami')"
    res2 = await sandbox.execute_python(code=os_sys_code)
    assert res2.status == SandboxStatus.SECURITY_BLOCKED.value


# ---------------------------------------------------------
# 6. Syntax Error & Runtime Failure Handling
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_sandbox_invalid_code_syntax_error(sandbox):
    bad_syntax_code = "def broken_func(\n   return 123"
    result = await sandbox.execute_python(code=bad_syntax_code)
    assert result.status == SandboxStatus.FAILURE.value
    assert result.exit_code != 0
    assert "SyntaxError" in result.stderr


@pytest.mark.asyncio
async def test_sandbox_runtime_exception(sandbox):
    runtime_err_code = "x = [1, 2, 3]\nprint(x[99])"
    result = await sandbox.execute_python(code=runtime_err_code)
    assert result.status == SandboxStatus.FAILURE.value
    assert result.exit_code != 0
    assert "IndexError" in result.stderr
