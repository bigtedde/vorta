import os
import sys
from pathlib import Path

import pytest
from PyQt6 import QtCore
from PyQt6.QtWidgets import QCheckBox, QFormLayout


@pytest.mark.skipif(sys.platform != "linux", reason="test only applicable on Linux")
def test_autostart_linux(qapp, qtbot):
    setting = "Automatically start Vorta at login"

    # ensure file is present when autostart is enabled
    _click_toggle_setting(setting, qapp, qtbot)
    autostart_path = (
        Path(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~") + '/.config') + "/autostart") / "vorta.desktop"
    )
    qtbot.waitUntil(lambda: autostart_path.exists(), **pytest._wait_defaults)
    with open(autostart_path) as desktop_file:
        desktop_file_text = desktop_file.read()
    assert desktop_file_text.startswith("[Desktop Entry]")

    # ensure file is removed when autostart is disabled
    _click_toggle_setting(setting, qapp, qtbot)
    if sys.platform == 'linux':
        assert not os.path.exists(autostart_path)


@pytest.mark.skipif(sys.platform != 'darwin', reason="Full Disk Access check only on Darwin")
def test_check_full_disk_access(qapp, qtbot, mocker):
    # tests "full disk access" check on darwin machines
    setting = "Check for Full Disk Access on startup"

    mocker.patch('pathlib.Path.exists', return_value=True)
    mocker.patch('os.access', return_value=False)
    mock_qmessagebox = mocker.patch('vorta.application.QMessageBox')

    # performing check is default, so we see that 'full disk access' message appears
    qapp.check_darwin_permissions()
    mock_qmessagebox.assert_called()
    expected_text = "Vorta needs Full Disk Access for complete Backups"
    mock_qmessagebox.return_value.setText.assert_called_once_with(expected_text)

    mock_qmessagebox.reset_mock()

    # toggle setting to disable check, see that pop-up does not occur
    _click_toggle_setting(setting, qapp, qtbot)
    qapp.check_darwin_permissions()
    mock_qmessagebox.assert_not_called()


def _click_toggle_setting(setting, qapp, qtbot):
    """Click toggle setting in the misc tab"""

    main = qapp.main_window
    main.tabWidget.setCurrentIndex(4)
    tab = main.miscTab

    for x in range(0, tab.checkboxLayout.count()):
        item = tab.checkboxLayout.itemAt(x, QFormLayout.ItemRole.FieldRole)
        if not item:
            continue
        checkbox = item.itemAt(0).widget()
        checkbox.__class__ = QCheckBox

        if checkbox.text() == setting:
            # Have to use pos to click checkbox correctly
            # https://stackoverflow.com/questions/19418125/pysides-qtest-not-checking-box/24070484#24070484
            qtbot.mouseClick(
                checkbox, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(2, int(checkbox.height() / 2))
            )
            break
