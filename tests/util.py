import os, re, subprocess

class DynVar:
    def __init__(self, default=None): self.stack = [default]
    def __call__(self, value=...):
        if value is ...:
            return self.stack[-1]
        self.stack.append(value)
        return self
    def __enter__(self): pass
    def __exit__(self, *args): self.stack.pop()

run_env = DynVar({})

def _run_eec(cmd, expected_ec=0):
    cmd = [str(x) for x in cmd]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=40, env={**os.environ, **run_env()})
    assert proc.returncode == expected_ec, f"Expected EC {expected_ec} but got {proc.returncode}.\ncmd: {cmd}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    return proc.stdout, proc.stderr

def runc(*cmd):
    out, err = _run_eec(cmd)
    assert err == "", f"Expected no STDERR, but got:\n{err}"
    return out

def run1(*cmd):
    out, err = _run_eec(cmd, expected_ec=1)
    assert out == "", f"Expected no STDOUT, but got:\n{out}"
    return err

def runbg(*cmd):
    cmd = [str(x) for x in cmd]
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, **run_env()})

def m(pattern, string):
    match = re.match(pattern, string, re.DOTALL)
    if not match:
        return None
    assert match.group(0) == string
    ret = []
    for index in range((match.lastindex or 0)+1):
        ret.append(match.group(index))
    return ret
