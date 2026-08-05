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
    def __init__(self, fhir_data: dict, bundle_entries: list[dict] | None = None) -> None:
        self.fhir: dict = fhir_data

        # When the input was a Bundle, the full list of entry resources is kept here
        # so that builders can look up related resources (Group, Location, etc.).
        self.bundle_entries: list[dict] = bundle_entries or []

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

    def next_attr_counter(self) -> int:
        """
        1-based counter for extension attribute numbering.
        Mirrors PHP UsdmBuildContext::nextAttributeCounter().
        """
        val = self._entity_counters.get("_attr_counter", 0) + 1
        self._entity_counters["_attr_counter"] = val
        return val

    # -------------------------------------------------------------------------
    # Factory helpers
    # -------------------------------------------------------------------------

    def make_code(self, code: str, decode: str) -> dict:
        """Build a full USDM Code object from raw code + decode strings (CDISC system)."""
        code_id = f"Code_{self._code_counter}"
        self._code_counter += 1
        return {
            "id": code_id,
            "code": code,
            "decode": decode,
            **CDISC_CODE_SYSTEM,
            "instanceType": "Code",
        }

    def make_code_with_system(
        self,
        code: str,
        decode: str,
        code_system: str,
        code_system_version: str,
    ) -> dict:
        """
        Build a USDM Code object with an explicit code system (e.g. SNOMED CT).
        Use for condition/indication codes that are not CDISC-coded.
        """
        code_id = f"Code_{self._code_counter}"
        self._code_counter += 1
        return {
            "id": code_id,
            "extensionAttributes": [],
            "code": code,
            "codeSystem": code_system,
            "codeSystemVersion": code_system_version,
            "decode": decode,
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
