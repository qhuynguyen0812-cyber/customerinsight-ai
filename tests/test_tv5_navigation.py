"""Streamlit smoke and native navigation coverage owned by TV5."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from components.layout import NAV_ITEMS


ROOT = Path(__file__).resolve().parents[1]


def test_every_navigation_target_exists() -> None:
    assert [filename for filename, _ in NAV_ITEMS] == [
        "0_Tong_quan.py", "1_Du_lieu.py", "2_Kham_pha_du_lieu.py", "3_Chon_K.py",
        "4_Phan_cum.py", "5_Ket_qua.py", "6_Thuat_toan.py",
    ]
    assert all((ROOT / "views" / filename).is_file() for filename, _ in NAV_ITEMS)


@pytest.mark.parametrize(
    "path",
    [ROOT / "app.py"] + [ROOT / "views" / filename for filename, _ in NAV_ITEMS],
)
def test_shell_and_every_page_start_without_exception(path: Path) -> None:
    app = AppTest.from_file(str(path)).run(timeout=30)
    assert not app.exception


def test_overview_renders_without_duplicating_shell_progress() -> None:
    app = AppTest.from_file(str(ROOT / "views" / "0_Tong_quan.py")).run()
    assert not app.exception
    assert len(app.title) == 1
    assert len(app.get("progress")) == 0


def test_app_constructs_and_runs_native_navigation() -> None:
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
    assert not app.exception
    assert len(app.get("progress")) >= 1
