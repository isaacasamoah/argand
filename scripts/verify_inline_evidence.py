"""Exercise inline evaluation and captured voice with simulated transport, real APIs."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json
with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':1280,'height':720});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script('''class FakePeer{iceGatheringState='complete';localDescription=null;constructor(){window.pc=this}createDataChannel(){return this.channel={readyState:'open',send:s=>{if(JSON.parse(s).type==='session.close')queueMicrotask(()=>this.channel.onmessage({data:JSON.stringify({type:'session.closed',reason:'close_requested'})}))},close(){this.readyState='closed'}}}async createOffer(){return {type:'offer',sdp:'fake'}}async setLocalDescription(s){this.localDescription=s}async setRemoteDescription(){this.channel.onmessage({data:JSON.stringify({type:'session.started'})})}addTrack(){}close(){}}window.RTCPeerConnection=FakePeer;navigator.mediaDevices.getUserMedia=async()=>new MediaStream();window.emit=e=>window.pc.channel.onmessage({data:JSON.stringify(e)});''')
 page.route('**/api/voice/session',lambda route:route.fulfill(json={'transport':{'sdp':'fake'}}))
 page.goto('http://127.0.0.1:18770');page.get_by_role('button',name='Talk it through',exact=True).click();page.get_by_role('button',name='End conversation',exact=True).wait_for()
 page.evaluate("emit({type:'session.input_transcript.delta',delta:'What is the horizontal axis?',start_ms:1,end_ms:5});emit({type:'session.output_transcript.delta',delta:'The horizontal axis represents the real part.',start_ms:6,end_ms:10})")
 page.get_by_role('button',name='Your practice',exact=False).click()
 page.evaluate("emit({type:'session.input_transcript.delta',delta:'What should I try?',start_ms:11,end_ms:15});emit({type:'session.output_transcript.delta',delta:'Try a point on the real axis and compare its cube with 8.',start_ms:16,end_ms:20})")
 page.get_by_role('button',name='End conversation',exact=True).click()
 page.wait_for_function("document.querySelector('.inline-evidence').textContent.includes('2 recorded responses')")
 page.locator('.inline-evidence > summary').click()
 assert page.locator('.evidence-response').count()==2
 assert 'Voice · lesson' in page.locator('.inline-evidence').inner_text() and 'Voice · practice' in page.locator('.inline-evidence').inner_text()
 page.get_by_role('button',name='Assess conversation',exact=True).click()
 page.wait_for_function("!document.querySelector('.evidence-actions button').disabled",timeout=300000)
 page.locator('.evidence-response > summary').first.click()
 assert page.locator('.evidence-check').count()>0
 page.evaluate('window.scrollTo(0,0)')
 page.screenshot(path='/home/isaac/vault/argand/prototype/evidence/inline-evidence-browser.png',full_page=True)
 page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 print('PASS: lesson/practice voice capture, inline live assessment, expandable evidence, mobile width; simulated voice transport.',flush=True)
 b.close()
