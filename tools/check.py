"""One-command check: the test suite, then the text lint. Exit code gates the commit."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.exit(subprocess.call([sys.executable, "-X", "utf8", "-m", "pytest", "-q", str(ROOT / "tests")], cwd=ROOT)
         or subprocess.call([sys.executable, "-X", "utf8", str(ROOT / "tools/fit.py"), "--selftest"], cwd=ROOT)
         or subprocess.call([sys.executable, "-X", "utf8", str(ROOT / "tools/batches.py"), "check"], cwd=ROOT))
