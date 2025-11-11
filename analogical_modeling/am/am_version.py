"""weka.classifiers.lazy.AM"""

from pathlib import Path
from sys import stderr
import configparser

DEFAULT_VERSION = "UNKNOWN"


class AMVersion:
    "Specify version of Analogical Modeling"
    def __init__(self):
        self.version = self.get_version()

    @staticmethod
    def get_version() -> str:
        """Return the version of Analogical Modeling"""
        props_path = Path("resources/weka/classifiers/lazy/AM/Description.props")
        if not props_path.exists():
            print("Description.props file not found in resources.", file=stderr)
            return DEFAULT_VERSION

        try:
            config = configparser.ConfigParser()
            content = props_path.read_text()
            # needs sections
            if not content.strip().startswith("[DEFAULT]"):
                content = "[DEFAULT]" + content
            config.read_string(content)

            return config["DEFAULT"].get("Version", DEFAULT_VERSION)
        except Exception as e:
            # this is called in a static block, so any uncaught errors would prevent
            # the whole system from loading! So we must catch everything.
            print(f"Failed to load version from Description.props: {e}", file=stderr)
            return DEFAULT_VERSION

    def main(self, _args: list[str]):
        print(self.get_version())
