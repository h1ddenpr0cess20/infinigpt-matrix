"""Module entrypoint for `python -m infinigpt`.

Runs the package CLI which validates config and starts the bot.
"""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
