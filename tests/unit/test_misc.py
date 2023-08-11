import os
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
import vorta.store.models
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


def test_enable_fixed_units(qapp, qtbot, mocker):
    """Tests the 'enable fixed units' setting to ensure the archive tab sizes are displayed correctly."""
    tab = qapp.main_window.archiveTab
    setting = "Use the same unit of measurement for archive sizes"

    # set mocks
    mock_setting = mocker.patch.object(vorta.views.archive_tab.SettingsModel, "get", return_value=Mock(value=True))
    mock_pretty_bytes = mocker.patch.object(vorta.views.archive_tab, "pretty_bytes")

    # with setting enabled, fixed units should be determined and passed to pretty_bytes as an 'int'
    tab.populate_from_profile()
    mock_pretty_bytes.assert_called()
    kwargs_list = mock_pretty_bytes.call_args_list[0].kwargs
    assert 'fixed_unit' in kwargs_list
    assert isinstance(kwargs_list['fixed_unit'], int)

    # disable setting and reset mock
    mock_setting.return_value = Mock(value=False)
    mock_pretty_bytes.reset_mock()

    # with setting disabled, pretty_bytes should be called with fixed units set to 'None'
    tab.populate_from_profile()
    mock_pretty_bytes.assert_called()
    kwargs_list = mock_pretty_bytes.call_args_list[0].kwargs
    assert 'fixed_unit' in kwargs_list
    assert kwargs_list['fixed_unit'] is None

    # use the qt bot to click the setting and see that the refresh_archive emit works as intended.
    with qtbot.waitSignal(qapp.main_window.miscTab.refresh_archive, timeout=5000):
        _click_toggle_setting(setting, qapp, qtbot)


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
    """Toggle setting checkbox in the misc tab"""
    miscTab = qapp.main_window.miscTab

    for x in range(miscTab.checkboxLayout.count()):
        item = miscTab.checkboxLayout.itemAt(x, QFormLayout.ItemRole.FieldRole)
        if item is not None:
            checkbox = item.itemAt(0).widget()
            if checkbox.text() == setting and isinstance(checkbox, QCheckBox):
                # Have to use pos to click checkbox correctly
                # https://stackoverflow.com/questions/19418125/pysides-qtest-not-checking-box/24070484#24070484
                pos = QtCore.QPoint(2, int(checkbox.height() / 2))
                qtbot.mouseClick(checkbox, QtCore.Qt.MouseButton.LeftButton, pos=pos)
                break
