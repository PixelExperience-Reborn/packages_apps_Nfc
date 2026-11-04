# P1 — NFC Android 17 / mondrian source and module-boundary audit

Date: 2026-11-04. **AUDIT ONLY; historical packages/apps/Nfc is not an Android17-compatible replacement.**

## Provenance and relocation

- Historical PixelExperience-Reborn `packages_apps_Nfc` branch `seventeen`: commit `e1ef5413108b7f419252cb177081f9b3804b3300` (Android 14 r21 merge, 2024-01-30). Old source root `packages/apps/Nfc` defines the `NfcNci` Soong module.
- **Official AOSP17 r1** NFC is `platform/packages/modules/Nfc`, commit `940212c440f57032a19cf0f90c7faa8eca48d546`, tree `da01c841e3238648d0ae33c3392c05f1552e63d5`. Source: https://android.googlesource.com/platform/packages/modules/Nfc/+/refs/tags/android-17.0.0_r1
- The official AOSP17 manifest already selects `platform/packages/modules/Nfc` at `packages/modules/Nfc`, plus `platform/prebuilts/module_sdk/Nfc` and vendor HAL sources `hardware/nxp/nfc`, `hardware/st/nfc`, `hardware/samsung/nfc`. It does **not** select `packages/apps/Nfc`.
- Since Android 16, NFC Services has been an optional updateable Mainline component. In AOSP17, `NfcNci/Android.bp` declares **two competing packaging variants**: platform `NfcNci` (SDK `core_platform`, platform certificate) and `NfcNciApex` (SDK `module_current`, NFC certificate). `apex/Android.bp` packages `NfcNciApex` and JNI library in `com.android.nfcservices`. Which variant is actually installed depends on product/release configuration, **not** merely on the presence of this repo in the manifest.
- **Never** checkout the archived PE repo into `packages/apps/Nfc` alongside the modern module to build a ROM: it duplicates the `NfcNci` Soong name and restores an old privileged/Binder implementation.

## Historical changes, reviewed separately

| Commit | Old change | Decision for AOSP17 |
| --- | --- | --- |
| `50f6b461fe37a5773a4d15d93c4a7f13d4574662` (2015) | `NFC_ON_DEFAULT` changed `true` → `false` in `NfcService` | **Do not cherry-pick**. Current user preference and first-boot behavior must be tested using the current NFC Mainline service; preserve user choice. |
| `2d87e1dcaabed959994540abf7c2afc7dc1663e8` (historical vendor interface) | Add `getNfcAdapterVendorInterface(String vendor)` returning `null` in `INfcAdapter.Stub` | **Do not cherry-pick**: the vendor call provides no implementation and its old Binder contract is not verified against Android17. Investigate genuine vendor needs through current AIDL HAL and interface/API tests. |
| `3e15ba4d710c7b1d6ba0ee6f9dafd069099f87f9` (2023) | Remove a `synchronized (NfcService.this)` block in `isSecureNfcEnabled()` to address a possible deadlock | **Do not cherry-pick** until comparing modern `NfcNci/src/com/android/nfc/NfcService.java` and thread-safety assumptions. Historical source fix alone is not proof of missing current fix. |

The archived NFC manifest uses `android.uid.nfc` shared user, privileged permissions and a persistent service. This is **not** an ordinary app and must not be transplanted on its own.

## Concrete mondrian device dependencies observed

At `LF52406/mondrian_android_device_xiaomi_sm8450-common` (`lineage-24.0`):

- `common.mk` includes `android.hardware.nfc-service.nxp` and `com.android.nfc_extras`, plus NFC/eSE/UICC feature permission XMLs.
- `BoardConfigCommon.mk` configures SKU-specific `vintf/manifest_nfc.xml` and `manifest_no_nfc.xml` using `TARGET_NFC_SUPPORTED_SKUS`. Verify inherited make variables and effective VINTF for mondrian, not just the source snippets.
- `vintf/manifest_nfc.xml` declares legacy secure-element HIDL 1.2 instances `eSE1`, `SIM1`, `SIM2`, and `vendor.qti.esepowermanager`. This does not by itself prove Android17 NFC **AIDL HAL** registration or framework matrix compatibility.
- `proprietary-files.txt` includes `vendor/lib64/libsn100u_fw.so` and eSE power-manager blobs; `mondrian` vendor files include `libnfc-nci.conf`, `libnfc-nxp.conf`, `libnfc-nxp_RF.conf`.

At `LF52406/mondrian_android_device_xiaomi_mondrian` (`lineage-24.0`):
- `device.mk` packages `NfcResMondrian` overlay.
- `overlay/Nfc/AndroidManifest.xml` targets `com.android.nfc`, `targetName="NfcCustomization"`; `res/values/config.xml` sets `config_skuSupportsSecureNfc` to `mondrian`.
- Validate overlayable policy, overlay application to installed NFC packaging variant, secure NFC SKU behavior and NFC settings. If the Mainline APEX `NfcNciApex` is selected, verify overlay activation and policy against that installed APK, not by assuming the platform APK behavior.

## Checks before product integration

1. Confirm whether `RELEASE_PACKAGE_NFC_STACK` selects `com.android.nfcservices` or `NfcNci`; ensure exactly one active NFC service, and inspect actual product package/installed paths. Do not unconditionally add either package.
2. Resolve NXP NFC HAL implementation, AIDL version/instance, VINTF compatibility matrix, service manifest fragments, firmware and vendor proprietary libraries. Avoid overlaying the Android17 HAL with archived custom vendor NFC app.
3. Validate NFC service SELinux domains, security and permission allowlists, factory reset/first boot and persisted enabled state.
4. Confirm `NfcCustomization` overlayable resources on AOSP17 and the secure-NFC SKU string/selector with active RRO.
5. Pass actual AOSP17 Soong/APEX build, target-files duplicate module/package check, `lshal`/`service list`, `dumpsys nfc` / `cmd nfc` (as supported), VINTF, CTS/VTS.
6. Test NFC tag discovery/read/write, card emulation/HCE, transit/payment flows where legally/test-wise available, secure element/eSE/UICC routing, toggling and reboot persistence on POCO F5 Pro / Redmi K60 (mondrian).

## Decision and acceptance

- [x] Official AOSP17 module relocation and immutable upstream commit/tree verified.
- [x] Historical NFC changes and legacy module boundary inventoried.
- [x] Device NXP NFC service, SKU/VINTF and mondrian overlay sources identified.
- [x] Host-only source-inventory regression check created for the archived fork.
- [ ] Targeted official AOSP17 NFC source sync and module declaration CI.
- [ ] Full AOSP17 Soong/APEX, NFC HAL, RRO and VINTF validation.
- [ ] NFC feature and secure-element runtime tests on mondrian.

**Decision:** retain official `packages/modules/Nfc` and module SDK in AOSP17. Keep the old `packages/apps/Nfc` fork as source history only; do not add it to an active profile, and do not claim NFC Android17 compatibility before build + device verification.
