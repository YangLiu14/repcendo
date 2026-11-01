"""Motion-specific envelopes selected after viewing the human references.

These bounds describe our authored demonstrations, not physiological
limits. Inputs come from the scene-matched, full-cycle bone measurements.
"""
import math

FRONT_RAISES = {"front_raise", "seated_front_raise"}


def front_raise_violations(name, samples, frames):
    if name not in FRONT_RAISES:
        raise ValueError("Unsupported front-raise comparison")
    expected = [(f, side) for f in frames for side in ("Left", "Right")]
    if not frames or [(s.get("frame"), s.get("side")) for s in samples] != expected:
        return ["incomplete_or_duplicate_samples"]
    failures = []
    peak = 1 + (frames[-1] - 1) // 2
    for sample in samples:
        elevation = sample.get("shoulderElevationDegrees")
        elbow = sample.get("elbowFlexionDegrees")
        if not all(isinstance(v, (int, float)) and math.isfinite(v)
                   for v in (elevation, elbow)):
            failures.append("non_finite_joint_measurement")
            continue
        if not (0 <= elevation <= 95 and 0 <= elbow <= 20):
            failures.append((sample["frame"], sample["side"], "raise_envelope"))
        if sample["frame"] in (frames[0], frames[-1]) and elevation > 25:
            failures.append((sample["frame"], sample["side"], "pre_raised_rest_pose"))
        if sample["frame"] == peak and not 80 <= elevation <= 95:
            failures.append((sample["frame"], sample["side"], "shoulder_height_peak"))
    return failures


def seated_alternate_raise_violations(samples, frames):
    """Neutral-grip raises alternate from a lowered hand beside the hip."""
    expected = [(f, side) for f in frames for side in ("Left", "Right")]
    if not frames or [(s.get("frame"), s.get("side")) for s in samples] != expected:
        return ["incomplete_or_duplicate_samples"]
    count = frames[-1] - frames[0]
    midpoint = frames[0] + count // 2
    peaks = {"Left": frames[0] + count // 4,
             "Right": frames[0] + 3 * count // 4}
    failures = []
    for sample in samples:
        frame, side = sample["frame"], sample["side"]
        elevation = sample.get("shoulderElevationDegrees")
        elbow = sample.get("elbowFlexionDegrees")
        if not all(isinstance(v, (int, float)) and math.isfinite(v)
                   for v in (elevation, elbow)):
            failures.append("non_finite_joint_measurement")
            continue
        if not (0 <= elevation <= 95 and 0 <= elbow <= 20):
            failures.append((frame, side, "raise_envelope"))
        waiting = (side == "Right" and frame <= midpoint) or (side == "Left" and frame >= midpoint)
        if (waiting or frame in (frames[0], frames[-1])) and elevation > 25:
            failures.append((frame, side, "waiting_arm_not_lowered"))
        if frame == peaks[side] and not 80 <= elevation <= 95:
            failures.append((frame, side, "shoulder_height_peak"))
    return failures


def alternate_curl_violations(samples, frames):
    """Keep the observed supinated curl at the side with a full alternating arc."""
    expected = [(f, side) for f in frames for side in ("Left", "Right")]
    if not frames or [(s.get("frame"), s.get("side")) for s in samples] != expected:
        return ["incomplete_or_duplicate_samples"]
    count = frames[-1] - frames[0]
    midpoint = frames[0] + count // 2
    peaks = {"Left": frames[0] + count // 4,
             "Right": frames[0] + 3 * count // 4}
    failures = []
    for sample in samples:
        frame, side = sample["frame"], sample["side"]
        elevation = sample.get("shoulderElevationDegrees")
        elbow = sample.get("elbowFlexionDegrees")
        if not all(isinstance(v, (int, float)) and math.isfinite(v)
                   for v in (elevation, elbow)):
            failures.append("non_finite_joint_measurement")
            continue
        if not 0 <= elevation <= 25:
            failures.append((frame, side, "upper_arm_too_far_from_side"))
        if not 10 <= elbow <= 125:
            failures.append((frame, side, "curl_envelope"))
        waiting = (side == "Right" and frame <= midpoint) or (side == "Left" and frame >= midpoint)
        if (waiting or frame in (frames[0], frames[-1])) and elbow > 30:
            failures.append((frame, side, "waiting_arm_not_lowered"))
        if frame == peaks[side] and not 100 <= elbow <= 120:
            failures.append((frame, side, "incomplete_curl_peak"))
    return failures


def cross_body_curl_violations(samples, frames):
    """Alternating cross-body curl with a lowered waiting hand.

    A small forward upper-arm offset accommodates the sculpture's chest;
    the selected demonstration must still avoid the old pre-raised arm.
    """
    expected = [(f, side) for f in frames for side in ("Left", "Right")]
    if not frames or [(s.get("frame"), s.get("side")) for s in samples] != expected:
        return ["incomplete_or_duplicate_samples"]
    count = frames[-1] - frames[0]
    midpoint = frames[0] + count // 2
    peaks = {"Left": frames[0] + count // 4,
             "Right": frames[0] + 3 * count // 4}
    failures = []
    for sample in samples:
        frame, side = sample["frame"], sample["side"]
        elevation = sample.get("shoulderElevationDegrees")
        elbow = sample.get("elbowFlexionDegrees")
        if not all(isinstance(v, (int, float)) and math.isfinite(v)
                   for v in (elevation, elbow)):
            failures.append("non_finite_joint_measurement")
            continue
        if not (0 <= elevation <= 30 and 10 <= elbow <= 125):
            failures.append((frame, side, "cross_body_curl_envelope"))
        waiting = (side == "Right" and frame <= midpoint) or (side == "Left" and frame >= midpoint)
        if (waiting or frame in (frames[0], frames[-1])) and elbow > 30:
            failures.append((frame, side, "waiting_arm_not_lowered"))
        if frame == peaks[side] and not 100 <= elbow <= 120:
            failures.append((frame, side, "incomplete_curl_peak"))
    return failures


def bilateral_curl_violations(name, samples, frames):
    """Selected seated-supinated and standing-reverse demonstrations only."""
    if name not in {"seated_curl", "reverse_curl"}:
        raise ValueError("Unsupported bilateral curl comparison")
    expected = [(f, side) for f in frames for side in ("Left", "Right")]
    if not frames or [(s.get("frame"), s.get("side")) for s in samples] != expected:
        return ["incomplete_or_duplicate_samples"]
    failures = []
    peak = frames[0] + (frames[-1] - frames[0]) // 2
    elevation_limit = 28 if name == "seated_curl" else 25
    for sample in samples:
        elevation, elbow = sample.get("shoulderElevationDegrees"), sample.get("elbowFlexionDegrees")
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (elevation, elbow)):
            failures.append("non_finite_joint_measurement")
            continue
        label = (sample["frame"], sample["side"])
        if not 0 <= elevation <= elevation_limit:
            failures.append((*label, "upper_arm_too_far_from_side"))
        if not 10 <= elbow <= 125:
            failures.append((*label, "curl_envelope"))
        if sample["frame"] in (frames[0], frames[-1]) and elbow > 30:
            failures.append((*label, "incomplete_lowering"))
        if sample["frame"] == peak and not 100 <= elbow <= 120:
            failures.append((*label, "incomplete_curl_peak"))
    return failures


def lateral_front_raise_violations(samples, frames):
    """Two shoulder-height repetitions with a lowered reset between planes."""
    expected = [(f, side) for f in frames for side in ("Left", "Right")]
    if not frames or [(s.get("frame"), s.get("side")) for s in samples] != expected:
        return ["incomplete_or_duplicate_samples"]
    count = frames[-1] - frames[0]
    resets = {frames[0], frames[0] + count // 2, frames[-1]}
    peaks = {frames[0] + count // 4, frames[0] + 3 * count // 4}
    failures = []
    for sample in samples:
        elevation, elbow = sample.get("shoulderElevationDegrees"), sample.get("elbowFlexionDegrees")
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (elevation, elbow)):
            failures.append("non_finite_joint_measurement")
            continue
        label = (sample["frame"], sample["side"])
        if not (0 <= elevation <= 95 and 0 <= elbow <= 20):
            failures.append((*label, "raise_envelope"))
        if sample["frame"] in resets and elevation > 30:
            failures.append((*label, "incomplete_lowering_between_planes"))
        if sample["frame"] in peaks and not 80 <= elevation <= 95:
            failures.append((*label, "shoulder_height_peak"))
    return failures


def single_curl_violations(samples, frames):
    """Selected standing left-arm curl; the free right arm stays lowered."""
    expected = [(f, side) for f in frames for side in ("Left", "Right")]
    if not frames or [(s.get("frame"), s.get("side")) for s in samples] != expected:
        return ["incomplete_or_duplicate_samples"]
    failures = []
    peak = frames[0] + (frames[-1] - frames[0]) // 2
    for sample in samples:
        if sample["side"] == "Right":
            drift = sample.get("unloadedArmDrift")
            if not isinstance(drift, (int, float)) or not math.isfinite(drift) or not 0 <= drift <= 1e-4:
                failures.append((sample["frame"], "Right", "free_arm_moved"))
            continue
        elevation = sample.get("shoulderElevationDegrees")
        elbow = sample.get("elbowFlexionDegrees")
        if not all(isinstance(v, (int, float)) and math.isfinite(v)
                   for v in (elevation, elbow)):
            failures.append("non_finite_joint_measurement")
            continue
        label = (sample["frame"], sample["side"])
        if not 0 <= elevation <= 25:
            failures.append((*label, "upper_arm_too_far_from_side"))
        if not 10 <= elbow <= 125:
            failures.append((*label, "curl_envelope"))
        if sample["frame"] in (frames[0], frames[-1]) and elbow > 30:
            failures.append((*label, "incomplete_lowering"))
        if sample["frame"] == peak and not 100 <= elbow <= 120:
            failures.append((*label, "incomplete_curl_peak"))
    return failures


def zottman_curl_violations(samples, frames):
    """Side-held upper arms through supinated lift, turn and reverse lowering."""
    expected = [(f, side) for f in frames for side in ("Left", "Right")]
    if not frames or [(s.get("frame"), s.get("side")) for s in samples] != expected:
        return ["incomplete_or_duplicate_samples"]
    count = frames[-1] - frames[0]
    peak_start, peak_end = frames[0] + 3*count//8, frames[0] + count//2
    low_start = frames[0] + 7*count//8
    failures = []
    for sample in samples:
        elevation, elbow = sample.get("shoulderElevationDegrees"), sample.get("elbowFlexionDegrees")
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (elevation, elbow)):
            failures.append("non_finite_joint_measurement")
            continue
        label = (sample["frame"], sample["side"])
        if not 0 <= elevation <= 25:
            failures.append((*label, "upper_arm_too_far_from_side"))
        if not 10 <= elbow <= 125:
            failures.append((*label, "curl_envelope"))
        if (sample["frame"] == frames[0] or sample["frame"] >= low_start) and elbow > 30:
            failures.append((*label, "incomplete_lowering"))
        if peak_start <= sample["frame"] <= peak_end and not 100 <= elbow <= 120:
            failures.append((*label, "incomplete_curl_peak"))
    return failures
