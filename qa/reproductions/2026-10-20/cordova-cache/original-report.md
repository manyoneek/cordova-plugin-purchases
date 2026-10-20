# iOS returns an empty object for an absent virtual currency cache

**Repository:** RevenueCat/cordova-plugin-purchases 8.2.4, commit `1e3266d79dcef0ce24b0a87fce10189143bc5886`.
**Reproduced on:** native Cordova iOS 8.0.1 / iOS 27.1 simulator, PurchasesHybridCommon 19.12.0 and RevenueCat iOS 5.95.0.

`getCachedVirtualCurrencies()` returns `{}` before currencies have been fetched and after the cache is invalidated. Its public contract says the value remains `null` until a fetch. A successful empty fetch correctly returns `{"all":{}}`.

## Reproduce

1. Build and launch the included CordovaRepro app (`build-repro.sh`; instructions in README).
2. Configure a fresh synthetic Test Store user and call `getCachedVirtualCurrencies()`.
3. Call `getVirtualCurrencies()`, read the populated cache, invalidate it, then read again.

**Expected:** `null` → `{"all":{}}` → `null`.
**Actual:** `{}` → `{"all":{}}` → `{}`.

A truthiness-based cache check can mistake the missing cache for loaded data; the returned object also lacks the required `all` field.

## Cause and solution

`src/ios/PurchasesPlugin+VirtualCurrencies.swift` replaces the shared library's nil result with `[:]`. Preserve a present dictionary and use `CDVPluginResult(status: .ok)` for the absent result; Cordova serializes its nil message as JavaScript `null`. The included patch passes the same app assertions.

## Evidence

`python3 run-native-regression.py before`: both absent-cache assertions fail; the fetched-cache control passes. With the diagnostic patch, `python3 run-native-regression.py fixed` passes all three. The complete shared app regression changes from **4 passed / 5 failed** to **9 passed / 0 failed**. Existing `npm test -- --runInBand`: **54 passed** before and with the fixes.

See [app source](../app/www/js/repro.js), [before screenshot](../evidence/before.png), [after screenshot](../evidence/fixed.png), [before video](../evidence/before.mp4), [after video](../evidence/fixed.mp4), [test logs](../native-before.log), [fixed logs](../native-fixed.log), and [solution](../suggested-fixes.patch).

App: **CordovaRepro**, bundle `com.revenuecat.sdkbugreporter.cordova`; RevenueCat **SDK Bug Reporter** (`proj602cc762`), **Test Store** (`app4ca00b430f`). [Dashboard](https://app.revenuecat.com/projects/602cc762/apps/app4ca00b430f).

**Limits:** real Test Store customer/currency responses and actual native implementation; no mocked transport. iOS simulator only, no Android or physical-device execution. The fetched balance control is an empty currency collection.

## Introduced in

[cordova-plugin-purchases #920](https://github.com/RevenueCat/cordova-plugin-purchases/pull/920) · merged 2026-04-09 · commit [`12ca77111807`](https://github.com/RevenueCat/cordova-plugin-purchases/commit/12ca771118072cfdb336b7db7254c6f14ec72c65). First stable source tag containing the change: **7.3.6**.

Regression from the Cordova iOS 8 compatibility change. The original currency implementation in [#705](https://github.com/RevenueCat/cordova-plugin-purchases/pull/705) preserved the optional cache. #920 added `?? [:]`. Executing the unchanged historical method before and after #920 changes an absent cache from `null` to `{}`; the populated-cache control remains `{"all":{}}`.

**Historical verification limits:** Historical method bodies compiled with a nullable result/recording Cordova shim. This isolates the fallback change; full historical Cordova runtime builds were not executed.

## Latest upstream recheck — 2026-10-20

**still-reproduces** at `f83961e065b9bf09684c2fda0156ce4564173881`. Actual current Swift method returns {} for an absent cache; populated-cache control preserves the dictionary.

Verification: Local regression revalidation; no new full mobile-app, backend, Android or physical-device execution. Evidence: `revalidation/2026-10-20/cordova-current-results.json`.
