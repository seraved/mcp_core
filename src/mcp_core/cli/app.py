from __future__ import annotations

import sys
from typing import Callable, Optional

import questionary


def run_cli_app(
    actions: dict[str, Optional[Callable[[], None]]],
    bye_msg: str = "Bye.",
) -> None:
    try:
        while True:
            choice = questionary.select("Action:", choices=list(actions.keys())).ask()

            if choice is None or actions[choice] is None:
                break

            actions[choice]()
            print()
    except KeyboardInterrupt:
        print(f"\n{bye_msg}")
        sys.exit(0)
