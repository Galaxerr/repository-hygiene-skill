import argparse
import importlib

from . import standard_renderer
from .service import RENDERERS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("standard", "extended"), default="standard")
    args = parser.parse_args()
    if args.profile == "extended":
        # Profile modules register renderers on import.
        importlib.import_module(f"{__package__}.{args.profile}_renderer")
    print(RENDERERS[args.profile]("sample"))


if __name__ == "__main__":
    main()
