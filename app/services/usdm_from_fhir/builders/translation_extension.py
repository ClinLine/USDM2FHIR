"""
build_translation_extension — USDM "languages" ExtensionAttribute builder.

Reverse-direction counterpart of BuildTranslationExtensionTrait.php /
buildTranslationExtension() in readi_core. Produces the exact same nested
USDM shape so a title/objective translation round-trips losslessly:

  ExtensionAttribute (url: .../languages)
    extensionAttributes[]
      ExtensionAttribute (url: .../language) — one per locale
        valueExtensionClass (url: .../class-1)
          extensionAttributes[]
            ExtensionAttribute url="language" valueCode -> ISO 639-1 Code
            ExtensionAttribute url="text"     valueString -> translated text
"""

from __future__ import annotations

from app.services.usdm_from_fhir.context import UsdmBuildContext
from app.services.usdm_from_fhir.codes import ISO_639_1

_CLASS_URL = "http://cdisc.org/usdm/extensions/extensionR-1/class-1"
_LANGUAGE_URL = "http://cdisc.org/usdm/extensions/extensionR-2/language"
_LANGUAGES_URL = "http://cdisc.org/usdm/extensions/extensionR-1/languages"


def build_translation_extension(context: UsdmBuildContext, values: list[tuple[str, str]]) -> dict:
    """
    values: list of (locale, text) pairs, one per non-default-locale translation.
    """
    language_entries = []

    for locale, text in values:
        n = context.next_attr_counter()
        decode = ISO_639_1.get(locale, locale)

        value_ext_class = {
            "id": f"ExtensionClass_Lan_{n}",
            "url": _CLASS_URL,
            "extensionAttributes": [
                {
                    "id": f"ExtensionAttributeValue_{n}",
                    "url": "language",
                    "extensionAttributes": [],
                    "valueCode": {
                        "id": f"CodeL_{n:03d}",
                        "code": locale,
                        "decode": decode,
                        "codeSystem": "ISO 639-1",
                        "codeSystemVersion": "2002",
                        "instanceType": "Code",
                    },
                    "instanceType": "ExtensionAttribute",
                },
                {
                    "id": f"ExtensionAttributeValue_{n}",
                    "url": "text",
                    "valueString": text,
                    "extensionAttributes": [],
                    "instanceType": "ExtensionAttribute",
                },
            ],
            "instanceType": "ExtensionClass",
        }

        language_entries.append({
            "id": f"extensionAttributes_{n}",
            "url": _LANGUAGE_URL,
            "valueExtensionClass": value_ext_class,
            "extensionAttributes": [],
            "instanceType": "ExtensionAttribute",
        })

    n = context.next_attr_counter()
    return {
        "id": f"ExtTransAttr_{n}",
        "url": _LANGUAGES_URL,
        "extensionAttributes": language_entries,
        "instanceType": "ExtensionAttribute",
    }