import pathlib

HELPER_ROOT = pathlib.Path(__file__).parent.resolve()
PROJECT_ROOT = HELPER_ROOT.parent.parent.parent.resolve()

CONFIG_PATH = PROJECT_ROOT / "config.toml"

SRC_ROOT = PROJECT_ROOT / "src"
SOURCE_ROOT = SRC_ROOT / "aitown"
REPO_ROOT = SOURCE_ROOT / "repos"
