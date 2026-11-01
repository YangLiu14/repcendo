"""Reference envelopes reject the defects found in the existing animations."""
import copy
import math
import unittest

from reference_motion_constraints import (
    alternate_curl_violations, bilateral_curl_violations,
    cross_body_curl_violations, front_raise_violations,
    lateral_front_raise_violations, seated_alternate_raise_violations,
    single_curl_violations, zottman_curl_violations,
)


def samples(count, alternating=False, raises=False, combination=False, zottman=False):
    rows = []
    for frame in range(1, count + 2):
        t = (frame - 1) / count
        for side in ('Left', 'Right'):
            if zottman:
                d = min(t / .375, 1) if t <= .5 else max((.875-t)/.375, 0)
            else:
                d = math.sin(math.pi*t*(2 if alternating or combination else 1))**2
                if alternating and ((side == 'Right' and t <= .5) or (side == 'Left' and t >= .5)):
                    d = 0
            rows.append(dict(frame=frame, side=side,
                             shoulderElevationDegrees=20+70*d if raises else 20,
                             elbowFlexionDegrees=10 if raises else 18+92*d))
    return rows, list(range(1, count + 2))


class ReferenceEnvelopeTests(unittest.TestCase):
    def cases(self):
        return [
            (lambda s, f: front_raise_violations('front_raise', s, f), samples(120, raises=True)),
            (lambda s, f: front_raise_violations('seated_front_raise', s, f), samples(120, raises=True)),
            (alternate_curl_violations, samples(192, alternating=True)),
            (cross_body_curl_violations, samples(192, alternating=True)),
            (seated_alternate_raise_violations, samples(192, alternating=True, raises=True)),
            (lateral_front_raise_violations, samples(192, combination=True, raises=True)),
            (lambda s, f: bilateral_curl_violations('seated_curl', s, f), samples(120)),
            (lambda s, f: bilateral_curl_violations('reverse_curl', s, f), samples(120)),
            (zottman_curl_violations, samples(192, zottman=True)),
        ]

    def test_complete_reference_envelopes(self):
        for check, (rows, frames) in self.cases():
            self.assertEqual(check(rows, frames), [])

    def test_missing_duplicate_and_reordered_measurements(self):
        for check, (rows, frames) in self.cases():
            for broken in (rows[:-1], rows + [rows[-1]], list(reversed(rows))):
                self.assertIn('incomplete_or_duplicate_samples', check(broken, frames))

    def test_non_finite_or_missing_angles_fail_closed(self):
        for check, (rows, frames) in self.cases():
            for key in ('shoulderElevationDegrees', 'elbowFlexionDegrees'):
                for value in (None, float('nan'), float('inf'), '20'):
                    broken = copy.deepcopy(rows)
                    broken[50][key] = value
                    self.assertIn('non_finite_joint_measurement', check(broken, frames))

    def test_old_raised_rest_is_rejected(self):
        rows, frames = samples(120, raises=True)
        rows[0]['shoulderElevationDegrees'] = 34
        self.assertIn((1, 'Left', 'pre_raised_rest_pose'), front_raise_violations('front_raise', rows, frames))

    def test_old_curl_shoulder_and_short_peak_are_rejected(self):
        rows, frames = samples(120)
        rows[120].update(shoulderElevationDegrees=34, elbowFlexionDegrees=90)
        errors = bilateral_curl_violations('reverse_curl', rows, frames)
        self.assertIn((61, 'Left', 'upper_arm_too_far_from_side'), errors)
        self.assertIn((61, 'Left', 'incomplete_curl_peak'), errors)

    def test_alternating_waiting_arm_cannot_lift(self):
        for check in (alternate_curl_violations, cross_body_curl_violations):
            rows, frames = samples(192, alternating=True)
            rows[97]['elbowFlexionDegrees'] = 75
            self.assertIn((49, 'Right', 'waiting_arm_not_lowered'), check(rows, frames))

    def test_combination_must_lower_between_planes(self):
        rows, frames = samples(192, combination=True, raises=True)
        rows[192]['shoulderElevationDegrees'] = 40
        self.assertIn((97, 'Left', 'incomplete_lowering_between_planes'), lateral_front_raise_violations(rows, frames))

    def test_zottman_turn_retains_flexion(self):
        rows, frames = samples(192, zottman=True)
        rows[160]['elbowFlexionDegrees'] = 85
        self.assertIn((81, 'Left', 'incomplete_curl_peak'), zottman_curl_violations(rows, frames))

    def test_single_arm_free_side_stability(self):
        rows, frames = samples(120)
        for row in rows:
            if row['side'] == 'Right':
                row.clear()
        # Free-side measurements intentionally contain drift, not loaded joint angles.
        for i in range(1, len(rows), 2):
            rows[i] = dict(frame=i//2+1, side='Right', unloadedArmDrift=0)
        self.assertEqual(single_curl_violations(rows, frames), [])
        for invalid in (.002, float('nan'), None):
            rows[61]['unloadedArmDrift'] = invalid
            self.assertIn((31, 'Right', 'free_arm_moved'), single_curl_violations(rows, frames))


if __name__ == '__main__':
    unittest.main()
