# iOS silently ignores null subscriber-attribute deletions

**Repository:** RevenueCat/cordova-plugin-purchases 8.2.4, commit `1e3266d79dcef0ce24b0a87fce10189143bc5886`.
**Reproduced on:** native Cordova iOS 8.0.1 / iOS 27.1 simulator, PurchasesHybridCommon 19.12.0 and RevenueCat iOS 5.95.0.

`setDisplayName(null)` leaves the previous name stored, despite its documented deletion behavior. A `null` value in the typed `setAttributes()` map rejects the entire map, including valid sibling updates. These void JavaScript methods provide no error callback, so the rejection is silent to the caller.

## Reproduce

1. Launch the included CordovaRepro app with a fresh synthetic Test Store user.
2. Call `setDisplayName("QA original name")` and `setAttributes({qa_null_delete:"original", qa_keep:"control"})`.
3. Call `setDisplayName(null)` and `setAttributes({qa_null_delete:null, qa_keep:"updated"})`.
4. Inspect the SDK's persisted attributes using the included read-only native observer. Repeat deletion with empty strings as a control.

**Expected:** both deleted values become the SDK's empty-string deletion marker; `qa_keep` becomes `"updated"`.
**Actual:** the old name and custom value remain; `qa_keep` stays `"control"`. Empty-string deletion succeeds.

Apps using the advertised null input fail to clear stored values, and mixed attribute batches lose their valid updates too.

## Cause and solution

`PurchasesPlugin+Attribution.swift` accepts only `NSString` in `setSubscriberAttribute` and only `[String: String]` in `setAttributes`. JSON null arrives as `NSNull` and fails these guards. Accept strings and nulls, normalize a scalar null to the supported empty-string deletion marker, and pass the validated `[String: Any]` map to the shared library, which already normalizes null values. The included patch preserves rejection of other input types.

## Evidence

`python3 run-native-regression.py before`: three null-deletion/mixed-update assertions fail; string-set and empty-string-delete controls pass. With the patch, `python3 run-native-regression.py fixed` passes all five attribute assertions. Overall: **4 passed / 5 failed → 9 passed / 0 failed**. Existing `npm test -- --runInBand`: **54 passed** before and with fixes.

See [app source](../app/www/js/repro.js), [read-only observer](../evidence-plugin/QAEvidence.m), [before screenshot](../evidence/before.png), [after screenshot](../evidence/fixed.png), [before video](../evidence/before.mp4), [after video](../evidence/fixed.mp4), [test logs](../native-before.log), [fixed logs](../native-fixed.log), and [solution](../suggested-fixes.patch).

App: **CordovaRepro**, bundle `com.revenuecat.sdkbugreporter.cordova`; RevenueCat **SDK Bug Reporter** (`proj602cc762`), **Test Store** (`app4ca00b430f`). [Dashboard](https://app.revenuecat.com/projects/602cc762/apps/app4ca00b430f).

**Limits:** real native setter execution and persisted SDK values; the observer never changes SDK state. Server-side attribute deletion is not asserted. Only display name and custom attributes were exercised; other setters sharing the helper and Android were not executed.

## Introduced in

[cordova-plugin-purchases #134](https://github.com/RevenueCat/cordova-plugin-purchases/pull/134) · merged 2022-06-29 · commit [`7ef935c1b5bb`](https://github.com/RevenueCat/cordova-plugin-purchases/commit/7ef935c1b5bb763c6c2511f1dd88587c5c946a00). First stable source tag containing the change: **3.0.0**.

Regression introduced by the Objective-C-to-Swift migration. The preceding Objective-C bridge forwards scalar null and mixed null/string maps. The migration introduced `as? NSString` and `as? [String: String]` guards, rejecting both. Historical execution reproduces both rejections while empty-string controls pass. The parent already documented null display-name deletion and typed attribute values as `string | null`; its pinned PHC 1.10.0 normalized nulls. The change also appears in prerelease tag `3.0.0-rc.1`.

**Historical verification limits:** Historical bridge methods executed with recording dependency shims. Parent shared-library normalization was source-checked, not run through a complete historical app or server.

## Latest upstream recheck — 2026-10-20

**still-reproduces** at `f83961e065b9bf09684c2fda0156ce4564173881`. Actual current Swift methods reject both scalar null and a mixed map containing null, dropping sibling updates. Empty-string scalar/map controls are forwarded.

Verification: Local regression revalidation; no new full mobile-app, backend, Android or physical-device execution. Evidence: `revalidation/2026-10-20/cordova-current-results.json`.
