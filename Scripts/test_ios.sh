#!/bin/bash
# Dedicated throwaway device; never wipes an existing simulator or personal data.
set -euo pipefail
cd "$(dirname "$0")/.."
runtime="${1:-com.apple.CoreSimulator.SimRuntime.iOS-26-3}"
device_type="${2:-com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro}"
qa_device_id=$(xcrun simctl create "Repcendo UI Tests" "$device_type" "$runtime")
trap 'xcrun simctl delete "$qa_device_id" >/dev/null 2>&1 || true' EXIT
xcrun simctl boot "$qa_device_id"
xcrun simctl bootstatus "$qa_device_id" -b
xcrun simctl ui "$qa_device_id" appearance "${REPCENDO_QA_APPEARANCE:-light}"
if [[ "${REPCENDO_QA_REDUCE_MOTION:-0}" == "1" ]]; then
  xcrun simctl spawn "$qa_device_id" defaults write com.apple.Accessibility ReduceMotionEnabled -bool YES
fi
result_path="build/UITests-$(date +%Y%m%d-%H%M%S).xcresult"
xcodebuild -project Repcendo.xcodeproj -scheme Repcendo \
  -destination "platform=iOS Simulator,id=$qa_device_id" \
  -parallel-testing-enabled NO -derivedDataPath build \
  -resultBundlePath "$result_path" CODE_SIGNING_ALLOWED=NO test
