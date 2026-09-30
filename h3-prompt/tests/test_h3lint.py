import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import h3lint  # noqa: E402

BASE_OK = """integrated_multimodal_description:
[Shot 1] Midnight inside a roadside diner. <Subject 1>, an investigator in a damp wool coat, sits opposite <Subject 2>.
0.00-1.40s: hold both subjects across the booth. 1.40-3.30s: <Subject 2> slides an envelope across the table. 3.30s-end: <Subject 1> stops it with two fingers.
<Subject 2> (S2): <d>[English] You were never here.</d>
One slow push-in across table height, keeping the two-shot.

overall_soundscape:
Rain against glass, refrigerator hum, paper sliding.

non_diegetic_music:
No score until the envelope stops."""

REF_OK = """subject_definitions:
<Subject 1> is the visible performer in <Picture 1>; preserve identity, face and framing.
<Audio 1> is the complete spoken performance for <Subject 1> (S1).

summary:
[reference generation + audio reuse] <Subject 1> performs <Audio 1> with visible lip synchronization.

retention_analysis:
<Subject 1>: fully_preserved - preserve identity from <Picture 1>.
<Audio 1>: fully_copy - reuse <Audio 1> as the timing track.

detailed_description:
[Shot 1] <Subject 1> faces the camera at eye level. <Subject 1> (S1): <d>[Korean] 안녕하세요.</d>

overall_soundscape:
N/A

non_diegetic_music:
N/A"""


def rules(p, **kw):
    return {k for k in h3lint.check(p, **kw) if not k.startswith("_")}


def test_clean_prompts():
    assert rules(BASE_OK) == set()
    assert rules(REF_OK) == set()
    assert h3lint.check(REF_OK)["_mode"] == "reference" and h3lint.check(BASE_OK)["_mode"] == "base"
    assert rules(BASE_OK, duration=(22 + 17 * 4) / 24) == set()          # 90 frames, 17k+5


def test_free_text_and_negatives():
    free = "A beautiful cinematic shot of a woman walking. No blur, no extra people. Do not cut."
    r = rules(free)
    assert "no_h3_grammar" in r and "negative_language" in r


def test_ref_order_and_tags():
    swapped = REF_OK.replace("summary:\n[reference generation + audio reuse]", "summary:\nSomething")
    assert "ref_summary_tag" in rules(swapped)
    missing = REF_OK.replace("overall_soundscape:\nN/A\n\n", "")
    assert "ref_headings" in rules(missing)
    undefined = REF_OK.replace("[Shot 1] <Subject 1> faces", "[Shot 1] <Subject 2> faces")
    assert "undefined_subject" in rules(undefined)
    no_copy = REF_OK.replace("fully_copy", "kept")
    assert "audio_retention" in rules(no_copy)
    voice_only = no_copy.replace("with visible lip synchronization", "as a voice reference")
    assert "audio_retention" not in rules(voice_only)
    aligned = "For the target video, at 0.00 seconds, <Picture 1> (from [Shot 1]) is fully referenced.\n\n" + BASE_OK
    assert "shot_numbers" not in rules(aligned)


def test_dialogue_rules():
    bad_fmt = BASE_OK.replace("<Subject 2> (S2): <d>[English] You were never here.</d>", "<d>You were never here.</d>")
    assert "dialogue_format" in rules(bad_fmt)
    untagged = BASE_OK.replace("<Subject 2> (S2): <d>[English] You were never here.</d>",
                               'She says, "You were never here."')
    assert "dialogue_untagged" in rules(untagged)
    unbalanced = BASE_OK.replace("</d>", "")
    assert "dialogue_tags" in rules(unbalanced)


def test_camera_cuts_timeline_length():
    busy = BASE_OK.replace("One slow push-in", "A pan, then a tilt, then a crane rise and a zoom")
    assert "camera_moves" in rules(busy)
    cut = BASE_OK.replace("3.30s-end:", "[Shot 2] 3.30s-end:")
    assert "cut_format" in rules(cut)
    assert "cut_format" not in rules(BASE_OK.replace("3.30s-end:", "[Shot 2] At 00:03.300 3.30s-end:"))
    backwards = BASE_OK.replace("1.40-3.30s", "3.40-1.30s")
    r = rules(backwards)
    assert "timeline_range" in r and "timeline_order" in r
    assert "timeline_outside" in rules(BASE_OK, duration=3.0)
    assert "frames_grid" in rules(BASE_OK, duration=4.0)                 # 96 frames
    assert "frames_long" in rules(BASE_OK, duration=(5 + 17 * 22) / 24)  # 379 frames
    assert "too_long" in rules(BASE_OK + "x" * 7000)


def test_dialogue_at_chunk_end():
    two = BASE_OK.replace("1.40-3.30s: <Subject 2> slides an envelope across the table.",
                          "1.40-3.30s: <Subject 2> (S2): <d>[English] Take it.</d>")
    assert "dialogue_at_chunk_end" in rules(two, chunk_ends=[3.5, 7.0])
    assert "dialogue_at_chunk_end" not in rules(two, chunk_ends=[5.0, 7.0])
    assert "dialogue_at_chunk_end" not in rules(two, chunk_ends=[3.5])        # only one chunk


def test_cli_report(tmp_path, capsys):
    (tmp_path / "a.txt").write_text(BASE_OK, encoding="utf-8")
    (tmp_path / "b.jsonl").write_text(json.dumps({"prompt": "Do not move. A man stands."}) + "\n"
                                      + json.dumps({"prompt": REF_OK}) + "\n", encoding="utf-8")
    (tmp_path / "c.json").write_text(json.dumps(["just words"]), encoding="utf-8")
    rep = tmp_path / "R.md"
    det = tmp_path / "d.jsonl"
    assert h3lint.main(["check", str(tmp_path), "--report", str(rep), "--details", str(det)]) == 0
    text = rep.read_text(encoding="utf-8")
    assert "prompts: 4   clean: 2" in text and "| no_h3_grammar | 2 |" in text
    assert "Do not move" not in text and "Do not move" not in det.read_text(encoding="utf-8")


def test_same_line_headings_pronouns_and_bare_refs():
    same_line = BASE_OK.replace("integrated_multimodal_description:\n[Shot 1]", "integrated_multimodal_description: [Shot 1]")
    assert rules(same_line) == set()
    mixed = BASE_OK.replace("<Subject 2>", "the waitress").replace("stops it with two fingers",
                                                                     "stops it with his fingers while she nods")
    assert "pronoun_mix" in rules(mixed)
    assert "pronoun_mix" not in rules(BASE_OK.replace("stops it with two fingers", "stops it with his fingers while she nods"))
    assert "bare_reference" in rules("Picture 1 (from Shot 1) aligns with the first frame.\n\n" + BASE_OK)
    reason = h3lint.check(BASE_OK.replace("<Subject 2> (S2): <d>[English]", "<d>"))["dialogue_format"]
    assert "1 without '<Subject N> (SN):'" in reason and "1 without [Language]" in reason


def test_shape_hides_words():
    sk = h3lint.shape(REF_OK)
    assert "subject_definitions:" in sk and "[Shot 1]" in sk and "<d> [Korean]" in sk and "</d>" in sk
    assert "안녕하세요" not in sk and "performer" not in sk and "w)" in sk


def test_pasted_copy_and_retention_references():
    retention_refs = REF_OK.replace("<Subject 1>: fully_preserved - preserve identity from <Picture 1>.",
                                    "<Subject 1> as seen in [Shot 1]: fully_preserved - preserve identity from <Picture 1>.")
    assert "shot_numbers" not in rules(retention_refs)
    pasted = REF_OK.replace(
        "[Shot 1] <Subject 1> faces the camera at eye level.",
        "[Shot 1] <Subject 1> faces the camera at eye level while the room light stays warm and even. "
        "<Audio 1>: fully_copy - reuse. detailed_description: [Shot 1] <Subject 1> faces the camera at eye level "
        "while the room light stays warm and even.")
    r = rules(pasted)
    assert "nested_heading" in r and "repeated_text" in r and "shot_numbers" not in r
