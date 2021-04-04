import filecmp
import shutil
from pathlib import Path
from typing import Union

import pytest
from packaging import version

from .plugin import shorten_path


def file_match(self, value: Union[str, Path], snapshot_name: Union[str, Path]):
    """
    Asserts that ``value`` equals the current value of the snapshot with the given ``snapshot_name``.

    If pytest was run with the --snapshot-update flag, the snapshot will instead be updated to ``value``.
    The test will fail if the value changed.
    """

    if isinstance(value, str):
        value_path = Path(value).absolute()
    else:
        value_path = value.absolute()

    if not value_path.is_file():
        raise TypeError("value_path must be a file")

    snapshot_path = self._snapshot_path(snapshot_name)

    if snapshot_path.exists() and not snapshot_path.is_file():
        raise AssertionError(
            "snapshot exists but is not a file: {}".format(shorten_path(snapshot_path))
        )

    if self._snapshot_update:
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        if value_path.exists():
            if filecmp.cmp(snapshot_path, value_path):
                shutil.copy(value_path, snapshot_path)
                self._updated_snapshots.append(snapshot_path)
        else:
            snapshot_path.touch()
            self._created_snapshots.append(snapshot_path)
    else:
        if value_path.exists():
            # pytest diffs before version 5.4.0 required expected to be on the left hand side.
            expected_on_right = version.parse(pytest.__version__) >= version.parse(
                "5.4.0"
            )
            try:
                if expected_on_right:
                    assert filecmp.cmp(value_path, snapshot_path)
                else:
                    assert filecmp.cmp(snapshot_path, value_path)
            except AssertionError as e:
                snapshot_diff_msg = str(e)
            else:
                snapshot_diff_msg = None

            if snapshot_diff_msg:
                snapshot_diff_msg = (
                    "value does not match the expected value in snapshot {}\n{}".format(
                        shorten_path(snapshot_path), snapshot_diff_msg
                    )
                )
                raise AssertionError(snapshot_diff_msg)
        else:
            raise AssertionError(
                "snapshot {} doesn't exist. (run pytest with --snapshot-update to create it)".format(
                    shorten_path(snapshot_path)
                )
            )
