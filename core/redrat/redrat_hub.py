import os
import time
import logging
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class RedRatHubManager:
    """Start and manage the local RedRatHub process used by the IR backend."""

    def __init__(self):
        self.repo_root = Path(__file__).resolve().parents[2]
        self.hub_dir = Path(os.getenv("REDRAT_HUB_DIR", self.repo_root / "setup_files" / "IR_blaster" / "RedRatHub-V8.01"))
        self.exe_path = self.hub_dir / "RedRatHub.exe"
        self.http_port = self._load_http_port()
        self.hub_url = f"http://127.0.0.1:{self.http_port}"
        self.irdata_files = self._load_irdata_files()
        self._process = None
        self._started_by_manager = False

    def _load_http_port(self):
        env_port = os.getenv("REDRAT_HTTP_PORT")
        if env_port:
            return int(env_port)

        hub_url = os.getenv("REDRAT_HUB_URL", "http://127.0.0.1:8080")
        parsed = urlparse(hub_url)
        return int(parsed.port or 8080)

    def _load_irdata_files(self):
        raw = os.getenv("REDRAT_IRDATA_FILES")
        if raw:
            paths = [Path(p.strip()) for p in raw.split(";") if p.strip()]
        else:
            paths = [
                Path("assets/ir_signals_redrat"),
                Path("assets/ir_signals"),
            ]

        resolved = []
        for path in paths:
            if not path.is_absolute():
                path = self.repo_root / path

            if path.is_dir():
                xml_files = sorted(path.glob("*.xml"))
                if not xml_files:
                    logger.warning(f"IR data directory '{path}' contains no XML files")
                resolved.extend(xml_files)
            elif path.is_file():
                resolved.append(path)
            else:
                logger.warning(f"IR data path not found: {path}")

        if not resolved:
            raise FileNotFoundError(
                "No IR data XML files were found. "
                "Check REDRAT_IRDATA_FILES or the default asset folders."
            )

        return resolved

    def is_running(self):
        try:
            response = requests.get(f"{self.hub_url}/api/redrats", timeout=1)
            return response.ok
        except requests.RequestException:
            return False

    def ensure_running(self, wait_seconds=20):
        if self.is_running():
            logger.info(f"RedRatHub already available at {self.hub_url}")
            logger.info("RedRatHub process was not started by this framework run and will not be stopped automatically.")
            self._started_by_manager = False
            return True

        if not self.exe_path.exists():
            raise FileNotFoundError(f"RedRatHub.exe not found at {self.exe_path}")

        command = [
            str(self.exe_path),
            "--irdata",
            *[str(path) for path in self.irdata_files],
            "--httpport",
            str(self.http_port),
        ]

        logger.info("Starting RedRatHub process")
        logger.debug("RedRatHub command: %s", command)

        startupinfo = None
        creationflags = 0
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        self._process = subprocess.Popen(
            command,
            cwd=str(self.hub_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        self._started_by_manager = True

        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            if self.is_running():
                logger.info(f"RedRatHub started successfully on port {self.http_port}")
                return True
            time.sleep(1)

        raise RuntimeError(f"RedRatHub did not become available within {wait_seconds} seconds")

    def stop(self):
        if not self._started_by_manager:
            logger.info("RedRatHub was not started by this framework run; leaving existing process running.")
            return

        if self._process is None:
            return

        if self._process.poll() is None:
            logger.info("Stopping RedRatHub process")
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()

        self._process = None
        self._started_by_manager = False


