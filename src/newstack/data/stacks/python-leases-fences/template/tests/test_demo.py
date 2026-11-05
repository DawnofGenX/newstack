from {{ package_name }} import demo as subject


def test_every_story_holds() -> None:
    for title, body, held in subject.stories():
        assert held, title
        assert len(body) >= 3


def test_the_pause_story_shows_the_lost_update() -> None:
    _title, body, held = subject.pause_story()
    assert held
    text = "\n".join(body)
    assert "lost update" in text
    assert "refused" in text


def test_renewal_story_reports_1900() -> None:
    assert subject.renewal_story()[2]


def test_the_timeline_keeps_its_contract() -> None:
    rows, kept = subject.timeline()
    assert kept
    assert any("refused" in row for row in rows)
    assert rows[-1].endswith("kept")


def test_the_timeline_refuses_a_pointless_pause() -> None:
    try:
        subject.timeline(1_000, 500)
    except ValueError as error:
        assert "never expires" in str(error)
    else:
        raise AssertionError("a pause inside the lease was accepted")


def test_render_prints_six_titles() -> None:
    text = subject.render()
    for number in range(1, 7):
        assert f"{number}. " in text
