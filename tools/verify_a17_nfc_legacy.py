#!/usr/bin/env python3
"""Host-only historical NFC inventory, NOT Android17 module compatibility."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = "{http://schemas.android.com/apk/res/android}"


def check(condition, label):
    if not condition:
        raise AssertionError(label)
    print("PASS: " + label)


def main():
    bp = (ROOT / "Android.bp").read_text(encoding="utf-8")
    java = (ROOT / "src/com/android/nfc/NfcService.java").read_text(encoding="utf-8")
    manifest = ET.parse(ROOT / "AndroidManifest.xml").getroot()
    check('name: "NfcNci"' in bp and 'platform_apis: true' in bp,
          "historical privileged NFC Soong module exists; do not co-install")
    check('certificate: "platform"' in bp and 'jni_libs: ["libnfc_nci_jni"]' in bp,
          "historical NFC JNI and platform signing markers exist")
    check('static final boolean NFC_ON_DEFAULT = false;' in java,
          "historical default-off behavior is inventoried, not approved")
    check('getNfcAdapterVendorInterface(String vendor)' in java
          and 'return null;' in java,
          "historical vendor Binder stub identified, not approved")
    check('public boolean isSecureNfcEnabled()' in java
          and 'return mIsSecureNfcEnabled;' in java,
          "historical synchronization change identified")
    check(manifest.get("package") == "com.android.nfc"
          and manifest.get(ANDROID + "sharedUserId") == "android.uid.nfc",
          "old NFC system package/shared UID identified")
    check((ROOT / "nci").is_dir() and (ROOT / "src").is_dir(),
          "original NFC component folders exist")
    print("PASS: legacy-source provenance/invariants only. Android17 NFC HAL/APEX NOT TESTED.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ET.ParseError) as e:
        print("FAIL:", e, file=sys.stderr)
        sys.exit(1)
