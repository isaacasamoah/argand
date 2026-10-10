"""Real local UI + SymPy; configured tutor calls may incur charges. Run against localhost:18770."""

import os
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

EVIDENCE_DIR = Path(
    os.environ.get(
        "ARGAND_EVIDENCE_DIR", str(Path(tempfile.gettempdir()) / "argand-evidence")
    )
)
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


with sync_playwright() as p:
    browser = p.chromium.launch()
    for width, height in [(1280, 720), (1728, 961), (390, 844)]:
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto("http://127.0.0.1:18770")
        page.get_by_role("button", name="Skip to practice").click()
        assert page.get_by_role("button", name="Cube this point").count() == 0
        assert page.get_by_role("button", name="Add this root").count() == 0
        page.wait_for_timeout(400)
        assert page.locator(".collected-roots").count() == 0
        page.get_by_label("Candidate modulus").fill("2")
        for i, angle in enumerate([0, 120, 240], 1):
            page.get_by_label("Candidate angle").fill(str(angle))
            page.get_by_text(f"{i} / 3 found:", exact=False).wait_for()
        page.locator(".practice-feedback").wait_for()
        page.get_by_label("Candidate angle").fill("360")
        page.wait_for_timeout(500)
        assert "3 / 3 found:" in page.locator(".collected-roots").inner_text()
        if width >= 900:
            assert page.evaluate(
                "document.querySelector('.practice-card').getBoundingClientRect().height <= innerHeight - 90"
            ), page.locator(".practice-card").bounding_box()
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
        page.screenshot(path=EVIDENCE_DIR / f"practice-explorer-{width}.png")
        page.get_by_role("button", name="Reset", exact=True).click()
        assert page.get_by_label("Candidate modulus").input_value() == "1"
        assert page.locator(".collected-roots").count() == 0
        page.locator("math-field").click()
        page.keyboard.type("2")
        page.get_by_role("button", name="Check this root").click()
        page.locator(".practice-feedback").wait_for()
        print(
            "PASS",
            width,
            height,
            "incorrect, three roots, duplicate, reset and typed entry",
            flush=True,
        )
        page.close()
    # A late exact result must not collect a point the learner has already moved away from.
    page = browser.new_page()
    held = []

    def delay_match(route):
        if route.request.post_data_json["angle"] == 120:
            held.append(route)
        else:
            route.continue_()

    page.route("**/api/practice/cube", delay_match)
    page.goto("http://127.0.0.1:18770")
    page.get_by_role("button", name="Skip to practice").click()
    page.get_by_label("Candidate modulus").fill("2")
    page.get_by_label("Candidate angle").fill("120")
    page.wait_for_timeout(400)
    assert held
    page.get_by_label("Candidate angle").fill("115")
    held[0].fulfill(
        json={
            "matches": True,
            "exact": "-1 + sqrt(3)*i",
            "point": [-1, 1.732],
            "cubed": [8, 0],
        }
    )
    page.wait_for_timeout(500)
    assert page.locator(".collected-roots").count() == 0
    print("PASS late verification cannot collect a stale candidate", flush=True)
    browser.close()
