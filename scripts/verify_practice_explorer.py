"""Real local UI + SymPy; no model calls. Run against localhost:18770."""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width,height in [(1280,720),(1728,961),(390,844)]:
  page=browser.new_page(viewport={'width':width,'height':height});page.goto('http://127.0.0.1:18770');page.get_by_role('button',name='Skip to practice').click()
  cube=page.get_by_role('button',name='Cube this point');add=page.get_by_role('button',name='Add this root')
  assert add.is_disabled()
  cube.click();page.get_by_text('Not at the target yet.',exact=False).wait_for();assert add.is_disabled()
  page.get_by_label('Candidate modulus').fill('2')
  for angle in [0,120,240]:
   page.get_by_label('Candidate angle').fill(str(angle));assert add.is_disabled()
   cube.click();page.get_by_text('Matches the target.',exact=False).wait_for();add.click();page.get_by_text('Root already added.',exact=False).wait_for()
   assert add.is_disabled()
  page.get_by_text('Every root you submitted checks out',exact=False).wait_for()
  page.get_by_label('Candidate angle').fill('360');cube.click();page.get_by_text('Root already added.',exact=False).wait_for();assert add.is_disabled()
  if width>=900:assert page.evaluate('document.documentElement.scrollHeight<=innerHeight'),page.evaluate('document.documentElement.scrollHeight')
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.screenshot(path=f'/home/isaac/vault/argand/prototype/evidence/practice-explorer-{width}.png')
  page.get_by_role('button',name='Reset',exact=True).click();assert page.get_by_label('Candidate modulus').input_value()=='1';assert add.is_disabled()
  page.locator('#step').fill('2');page.get_by_role('button',name='Check answer').click();page.get_by_text('These roots work.',exact=False).wait_for()
  print('PASS',width,height,'incorrect, three roots, duplicate, reset and typed entry',flush=True);page.close()
 browser.close()
