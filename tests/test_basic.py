def test_main_file_exists():
    from pathlib import Path

    assert Path("main.py").exists()
