"""
AbstractSectionBuilder — Python equivalent of UsdmSectionBuilderInterface.php.

Each concrete builder:
  - declares get_key()      → dot-notation path in the context bag
  - declares get_priority() → execution order (lower = runs first)
  - implements build(ctx)   → returns the built section (list / dict / scalar)

FhirToUsdmService collects all builders, sorts by priority, runs them in order
and stores each result in the context bag under get_key().
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.usdm_from_fhir.context import UsdmBuildContext


class AbstractSectionBuilder(ABC):

    @abstractmethod
    def get_key(self) -> str:
        """
        Dot-notation path where the result is stored in the context bag.
        Examples:
          'version.titles'
          'version.studyIdentifiers'
          'version.studyDesign.objectives'
        """

    @abstractmethod
    def get_priority(self) -> int:
        """
        Execution order — lower number runs first.
        studyDesign.* builders must finish before any builder that reads them.
        """

    @abstractmethod
    def build(self, context: UsdmBuildContext):
        """Build and return the section value."""

