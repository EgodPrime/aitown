import pathlib

HELPER_ROOT = pathlib.Path(__file__).parent.resolve()
PROJECT_ROOT = HELPER_ROOT.parent.parent.parent.resolve()
SRC_ROOT = PROJECT_ROOT / "src"
SOURCE_ROOT = SRC_ROOT / "aitown"
REPO_ROOT = SOURCE_ROOT / "repos"  
