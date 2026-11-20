from mixmatch.export.tracklist import Entry, clock, cue_index, cue_sheet, tracklist

ENTRIES = [
    Entry("Paper Lights", "Oda Kray", 0.0),
    Entry('Rift "Dub"', None, 412.5),
    Entry("Low Sun", "Haldor", 3725.2),
]


def test_clock() -> None:
    assert [clock(0), clock(125.9), clock(3725)] == ["0:00", "2:05", "1:02:05"]


def test_cue_index_counts_frames_and_long_minutes() -> None:
    assert cue_index(0) == "00:00:00"
    assert cue_index(412.5) == "06:52:38"  # 0,5 s = 37,5 → 38 de cadre
    assert cue_index(3725.2) == "62:05:15"  # minutele trec de 59


def test_tracklist_text() -> None:
    assert tracklist("Set de vineri", ENTRIES) == (
        "Set de vineri\n\n"
        "01. [0:00] Oda Kray — Paper Lights\n"
        '02. [6:52] Rift "Dub"\n'
        "03. [1:02:05] Haldor — Low Sun\n"
    )


def test_cue_sheet() -> None:
    cue = cue_sheet("Set de vineri", "Set de vineri.mp3", "mp3", ENTRIES)
    assert cue.splitlines() == [
        'TITLE "Set de vineri"',
        'FILE "Set de vineri.mp3" MP3',
        "  TRACK 01 AUDIO",
        '    TITLE "Paper Lights"',
        '    PERFORMER "Oda Kray"',
        "    INDEX 01 00:00:00",
        "  TRACK 02 AUDIO",
        "    TITLE \"Rift 'Dub'\"",
        "    INDEX 01 06:52:38",
        "  TRACK 03 AUDIO",
        '    TITLE "Low Sun"',
        '    PERFORMER "Haldor"',
        "    INDEX 01 62:05:15",
    ]
    assert cue_sheet("X", "x.wav", "wav", ENTRIES[:1]).splitlines()[1] == 'FILE "x.wav" WAVE'
