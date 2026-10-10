"""Exercise single-root collection through the real UI and configured tutor."""

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
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 720})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://127.0.0.1:18770")
    page.get_by_role("button", name="Skip to practice").click()
    field = page.locator("math-field")
    field.click()
    page.keyboard.type("2")
    page.get_by_role("button", name="Check this root").click()
    page.get_by_text("1 / 3 found:", exact=False).wait_for(timeout=30000)
    assert field.evaluate("(e)=>e.value") == ""
    page.get_by_label("Candidate modulus").fill("2")
    page.get_by_label("Candidate angle").fill("120")
    page.get_by_text("2 / 3 found:", exact=False).wait_for(timeout=30000)
    field.click()
    page.keyboard.type("-1-")
    page.get_by_role("button", name="Square root", exact=True).click()
    page.keyboard.type("3")
    page.keyboard.press("ArrowRight")
    page.get_by_role("button", name="Imaginary unit", exact=True).click()
    print("Editor:", field.evaluate('(e)=>e.getValue("ascii-math")'), flush=True)
    page.get_by_role("button", name="Check this root").click()
    page.get_by_text("3 / 3 found:", exact=False).wait_for(timeout=30000)
    assert field.evaluate("(e)=>e.value") == ""
    field.click()
    page.keyboard.type("8")
    with page.expect_response(
        lambda r: r.url.endswith("/api/attempts") and r.request.method == "POST",
        timeout=30000,
    ) as response:
        page.get_by_role("button", name="Check this root").click()
    assert response.value.json()["checker"]["status"] == "incorrect"
    assert len(response.value.json()["collected_roots"]) == 3
    assert field.evaluate("(e)=>e.value") == "8"
    page.get_by_text("My working", exact=True).click()
    page.get_by_label("Notes to discuss with Argand · not checked").fill(
        "Cubing triples the angle. Why three roots?"
    )
    page.get_by_text("My working", exact=True).click()
    page.get_by_role("button", name="Revisit the lesson").click()
    page.get_by_role("button", name="Your practice Find the missing roots").click()
    assert "3 / 3 found:" in page.locator(".collected-roots").inner_text()
    for width, height in [(1280, 720), (1728, 961), (390, 844)]:
        page.set_viewport_size({"width": width, "height": height})
        page.screenshot(path=EVIDENCE_DIR / f"root-entry-{width}.png")
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
        if width > 900:
            assert page.evaluate(
                "document.querySelector('.practice-card').getBoundingClientRect().height <= innerHeight - 90"
            ), page.locator(".practice-card").bounding_box()
    assert not errors, errors
    print(
        "PASS mixed typed/visual roots, symbol keypad, retained invalid input, notes, navigation and screen fit",
        flush=True,
    )
    b.close()
