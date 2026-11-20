from mixmatch.text import sort_key


def test_sort_ignores_diacritics_and_case() -> None:
    names = ["Vârf de seară", "încălzire", "Șampanie", "Apus", "Stele"]
    assert sorted(names, key=sort_key) == [
        "Apus",
        "încălzire",
        "Șampanie",
        "Stele",
        "Vârf de seară",
    ]
