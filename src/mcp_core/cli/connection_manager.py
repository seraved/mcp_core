from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal, get_origin

from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True


class ConnectionManagerCLI:
    def __init__(
        self,
        model: type,
        config_path: str,
        secret_fields: list[str] | None = None,
        env_file: str | None = None,
    ):
        self.model = model
        self.config_path = Path(config_path)
        self.secret_fields = secret_fields or []
        self.env_file = Path(env_file) if env_file else None

    def _load_raw(self) -> dict:
        with open(self.config_path, "r", encoding="utf-8") as fh:
            data = yaml.load(fh)
        if data is None:
            data = {}
        if "connections" not in data:
            data["connections"] = {}
        return data

    def _save_raw(self, data: dict) -> None:
        with open(self.config_path, "w", encoding="utf-8") as fh:
            yaml.dump(data, fh)

    def add(self, key: str, values: dict, secrets: dict[str, str] | None = None) -> None:
        self.model.model_validate(values)  # raises on invalid input

        data = self._load_raw()
        data["connections"][key] = values
        self._save_raw(data)

        if secrets and self.env_file:
            self._upsert_env(secrets)

    def list(self) -> dict[str, Any]:
        return self._load_raw()["connections"]

    def remove(self, key: str) -> None:
        data = self._load_raw()
        data["connections"].pop(key, None)
        self._save_raw(data)

    def _upsert_env(self, secrets: dict[str, str]) -> None:
        existing_lines: list[str] = []
        if self.env_file.exists():
            existing_lines = self.env_file.read_text(encoding="utf-8").splitlines()

        updated_lines = [
            line
            for line in existing_lines
            if "=" not in line or line.split("=", 1)[0] not in secrets
        ]
        for var_name, value in secrets.items():
            updated_lines.append(f"{var_name}={value}")

        self.env_file.parent.mkdir(parents=True, exist_ok=True)
        content = "\n".join(updated_lines) + "\n"
        fd = os.open(self.env_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, content.encode("utf-8"))
        finally:
            os.close(fd)

    def run(self) -> None:  # pragma: no cover - interactive terminal I/O, tested manually per Task 13
        import questionary

        action = questionary.select(
            "What do you want to do?", choices=["add", "edit", "list", "remove"]
        ).ask()

        if action == "list":
            for key, values in self.list().items():
                print(f"{key}: {values}")
            return

        if action == "remove":
            key = questionary.text("Connection key to remove:").ask()
            self.remove(key)
            return

        key = questionary.text("Connection key:").ask()
        values, secrets = self._prompt_for_model_fields()
        self.add(key, values, secrets)

    def _prompt_for_model_fields(self) -> tuple[dict, dict]:  # pragma: no cover - interactive terminal I/O
        import questionary

        values: dict = {}
        secrets: dict[str, str] = {}
        for field_name, field_info in self.model.model_fields.items():
            values[field_name] = questionary.text(f"{field_name}:").ask()
        for secret_field in self.secret_fields:
            var_name = questionary.text(f"env var name for {secret_field}:").ask()
            secret_value = questionary.password(f"value for {var_name}:").ask()
            secrets[var_name] = secret_value
        return values, secrets


def discriminator_field_name(model: type) -> str | None:
    fields = getattr(model, "model_fields", None)
    if fields is None:
        return None
    for field_name, field_info in fields.items():
        if get_origin(field_info.annotation) is Literal:
            return field_name
    return None
