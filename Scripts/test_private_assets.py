"""Exercise real Git histories so tip-only checks cannot pass these tests."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from check_private_assets import inspect_history, push_revisions


class PrivateAssetsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.run_git("init", "-q")
        self.run_git("config", "user.email", "test@example.invalid")
        self.run_git("config", "user.name", "Asset policy test")

    def run_git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args])

    def commit_file(self, path, content=b"fixture"):
        dest = self.repo/path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        self.run_git("add", "--", path)
        self.run_git("commit", "-qm", "fixture")
        return self.run_git("rev-parse", "HEAD").decode().strip()

    def test_deleted_asset_still_blocks_history(self):
        path = "docs/animation-library/male/example.mp4"
        self.commit_file(path)
        self.run_git("rm", "--", path)
        self.run_git("commit", "-qm", "removed")
        self.assertTrue(inspect_history(self.repo, ["HEAD"], set())[0])

    def test_renaming_removed_content_does_not_bypass_check(self):
        self.commit_file("notes.txt", b"old-private-asset")
        blob = self.run_git("rev-parse", "HEAD:notes.txt").decode().strip()
        self.assertTrue(inspect_history(self.repo, ["HEAD"], {blob})[0])

    def test_text_metadata_and_ui_icon_are_allowed(self):
        self.commit_file("Repcendo/Resources/ExerciseAnimations/catalog.json", b"{}")
        self.commit_file("Repcendo/Assets.xcassets/AppIcon.appiconset/AppIcon.png")
        self.assertFalse(inspect_history(self.repo, ["HEAD"], set())[0])

    def test_annotated_tag_and_internal_tree_are_checked(self):
        self.commit_file("docs/character-assets/custom.newformat")
        self.run_git("tag", "-am", "old", "old")
        for revision in ("old", "HEAD^{tree}"):
            self.assertTrue(inspect_history(self.repo, [revision], set())[0])

    def test_submodule_contents_are_not_followed(self):
        oid = self.commit_file("README.md")
        self.run_git("update-index", "--add", "--cacheinfo", "160000,"+oid+",third_party/exercises-dataset")
        self.run_git("commit", "-qm", "gitlink")
        self.assertFalse(inspect_history(self.repo, ["HEAD"], set())[0])

    def test_push_only_checks_local_objects_and_allows_ref_deletion(self):
        oid = "a" * 40
        self.assertEqual(push_revisions([f"main {oid} refs/heads/main {'b'*40}\n"]), [oid])
        self.assertEqual(push_revisions([f"(delete) {'0'*40} refs/heads/old {oid}\n"]), [])
        with self.assertRaises(ValueError):
            push_revisions([f"snapshot {oid} refs/codex/backup {'0'*40}\n"])
        with self.assertRaises(ValueError):
            push_revisions(["invalid"])


if __name__ == "__main__":
    unittest.main()
