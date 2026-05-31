import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from checkin import is_already_checked_in_message


def test_already_checked_in_chinese_message_is_success():
    assert is_already_checked_in_message('今日已签到') is True
    assert is_already_checked_in_message('已经签到过了') is True
    assert is_already_checked_in_message('重复签到') is True


def test_already_checked_in_english_message_is_success():
    assert is_already_checked_in_message('already checked in today') is True
    assert is_already_checked_in_message('already signed') is True


def test_other_error_is_not_already_checked_in():
    assert is_already_checked_in_message('invalid session') is False
