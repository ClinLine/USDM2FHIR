"""
UsdmBuildContext — shared state passed through every builder.

Mirrors UsdmBuildContext.php from readi_core:
  - carries the source FHIR resource dict
  - owns all auto-increment counters (IDs are globally unique per build)
  - exposes factory helpers (make_code, lookup_code)
  - stores builder results via a dot-notation bag (set / get)
"""

from __future__ import annotations

from app.services.usdm_from_fhir.codes import CDISC_CODE_SYSTEM


class UsdmBuildContext:
    def __init__(self, fhir_data: dict) -> None:
        self.fhir: dict = fhir_data

        # Global counters — unique across all builders in the same build
        self._code_counter: int = 1
        self._entity_counters: dict[str, int] = {}

        # Dot-notation result bag
        self._bag: dict = {}

    # -------------------------------------------------------------------------
    # Dot-notation bag
    # -------------------------------------------------------------------------

    def set(self, path: str, value) -> None:
        """Store *value* at the dot-notation *path*."""
        keys = path.split(".")
        node = self._bag
        for key in keys[:-1]:
            node = node.setdefault(key, {})
        node[keys[-1]] = value

    def get(self, path: str, default=None):
        """Retrieve the value at *path*, or *default* if absent."""
        node = self._bag
        for key in path.split("."):
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    # -------------------------------------------------------------------------
    # Counter helpers
    # -------------------------------------------------------------------------

    def next_id(self, prefix: str) -> str:
        """Return a globally-unique id like 'Objective_0', 'Objective_1', …"""
        idx = self._entity_counters.get(prefix, 0)
        self._entity_counters[prefix] = idx + 1
        return f"{prefix}_{idx}"

    # -------------------------------------------------------------------------
    # Factory helpers
    # -------------------------------------------------------------------------

    def make_code(self, code: str, decode: str) -> dict:
        """Build a full USDM Code object from raw code + decode strings."""
        code_id = f"Code_{self._code_counter}"
        self._code_counter += 1
        return {
            "id": code_id,
            "code": code,
            "decode": decode,
            **CDISC_CODE_SYSTEM,
            "instanceType": "Code",
        }

    def lookup_code(self, table: dict[str, dict], fhir_value: str | None) -> dict | None:
        """
        Turn a FHIR coded value into a USDM Code object via *table*.
        Returns None (and prints a warning) when the value is absent or unknown,
        so callers can skip the field rather than guess.
        """
        if fhir_value is None:
            return None
        entry = table.get(fhir_value)
        if entry is None:
            print(f"[UsdmBuildContext] Warning: no lookup entry for FHIR code '{fhir_value}', skipping.")
            return None
        return self.make_code(entry["code"], entry["decode"])
