"""
Modular Skill Package Manager

Handles installation, uninstallation, and management of skill packages.
Supports Python wheels and Docker images.
"""

import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from packaging.version import Version

logger = logging.getLogger(__name__)


class SkillPackageManager:
    def __init__(self, skills_dir: str = "apps/h-core/src/skills/packages"):
        self.skills_dir = Path(skills_dir)
        self.skills_dir.mkdir(exist_ok=True)
        self.installed_packages: Dict[str, Dict] = {}
        self._load_installed_packages()

    def _load_installed_packages(self):
        """Load installed packages from manifest files."""
        self.installed_packages = {}
        for manifest_file in self.skills_dir.glob("*.manifest.yaml"):
            try:
                with open(manifest_file, "r") as f:
                    manifest = yaml.safe_load(f)
                    pkg_name = manifest.get("name", manifest_file.stem)
                    self.installed_packages[pkg_name] = manifest
            except Exception as e:
                logger.error(f"Failed to load {manifest_file}: {e}")

    async def install_package(self, package_url: str, package_name: Optional[str] = None):
        """Install a skill package from URL (pip wheel or git)."""
        if not package_name:
            package_name = package_url.split("/")[-1].split(".")[0]

        logger.info(f"Installing skill package: {package_name} from {package_url}")

        # Install via pip (for Python wheels)
        if package_url.endswith(".whl"):
            cmd = [sys.executable, "-m", "pip", "install", package_url, "--target", str(self.skills_dir)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Install failed: {result.stderr}")
                return False

        # Create manifest
        manifest = {
            "name": package_name,
            "url": package_url,
            "installed_at": str(datetime.now()),
            "version": "unknown",
        }

        manifest_file = self.skills_dir / f"{package_name}.manifest.yaml"
        with open(manifest_file, "w") as f:
            yaml.dump(manifest, f)

        self._load_installed_packages()
        logger.info(f"Skill package {package_name} installed")
        return True

    async def uninstall_package(self, package_name: str):
        """Uninstall a skill package."""
        logger.info(f"Uninstalling skill package: {package_name}")

        manifest_file = self.skills_dir / f"{package_name}.manifest.yaml"
        if manifest_file.exists():
            manifest_file.unlink()

        # Remove package files (simplified)
        pkg_dir = self.skills_dir / package_name
        if pkg_dir.exists():
            import shutil

            shutil.rmtree(pkg_dir)

        if package_name in self.installed_packages:
            del self.installed_packages[package_name]

        logger.info(f"Skill package {package_name} uninstalled")
        return True

    def list_packages(self) -> List[Dict]:
        """List all installed packages."""
        return list(self.installed_packages.values())

    def get_package(self, package_name: str) -> Optional[Dict]:
        """Get package details."""
        return self.installed_packages.get(package_name)

    async def upgrade_package(self, package_name: str):
        """Upgrade a package to latest version."""
        pkg = self.get_package(package_name)
        if not pkg:
            return False

        url = pkg.get("url")
        if url:
            return await self.install_package(url, package_name)

        return False


if __name__ == "__main__":
    manager = SkillPackageManager()
    print(manager.list_packages())
