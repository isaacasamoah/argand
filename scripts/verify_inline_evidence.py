"""Browser integration: simulated voice/evaluator; real evidence persistence."""
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
 calls=[]
 def evaluation(route):
  calls.append(route.request.url)
  route.fulfill(json={'rows':[{'id':str(i),'title':title,'requirement':title,'state':state,'probability':probability} for i,(title,state,probability) in enumerate([('Honest verification','pass',.9),('Useful next step','uncertain',.5),('No invented actions','fail',.1)])]})
 page.route('**/api/attempts/*/evaluate',evaluation)
 page.get_by_role('button',name='Evaluate',exact=True).click()
 page.wait_for_function("document.querySelector('.evaluation-overall')?.textContent.includes('2 of 2')")
 assert page.get_by_role('button',name='End conversation',exact=True).count()==1
 assert len(calls)==2
 page.get_by_text('Turn-by-turn results',exact=True).click()
 assert page.locator('.evidence-response').count()==2
 page.locator('.evidence-response > summary').first.click()
 assert page.locator('strong[aria-label=uncertain]').first.inner_text()=='•'
 page.evaluate("emit({type:'session.output_transcript.delta',delta:' Look at the cubed point.',start_ms:21,end_ms:25})")
 page.get_by_role('button',name='Evaluate',exact=True).click()
 page.wait_for_function("document.querySelector('.evidence-response:last-child').textContent.includes('Look at the cubed point.')")
 page.wait_for_function("!Array.from(document.querySelectorAll('button')).some(b=>b.textContent==='Evaluating…')")
 assert len(calls)==3 and page.locator('.evidence-response').count()==2
 page.get_by_role('button',name='End conversation',exact=True).click()
 page.get_by_role('button',name='Talk it through',exact=True).wait_for()
 assert page.locator('.evidence-response').count()==2
 # Simulate the answer service completing the collection; assert UI auto-evaluates.
 attempt={'id':'browser-completion','student':'2','tutor':'All roots are collected. Explain why the list is complete.','tutor_source':'test fixture','action':'collect','collected_roots':['2','-1+sqrt(3)*i','-1-sqrt(3)*i'],'collection_points':[[2,0],[-1,1.732],[-1,-1.732]],'checker':{'status':'complete','detail':'Complete','points':[],'valid':[True]},'versions':{},'evidence':{'T1':'All roots are collected.'}}
 page.route('**/api/attempts',lambda route:route.fulfill(json=attempt))
 page.locator('math-field').evaluate("e=>{e.value='2';e.dispatchEvent(new Event('input',{bubbles:true}))}")
 page.get_by_role('button',name='Check this root',exact=True).click()
 page.wait_for_function("document.querySelector('.evaluation-overall')?.textContent.includes('3 of 3')")
 assert len(calls)==4
 assert page.locator('header').get_by_text('Learning space',exact=True).count()==0
 page.evaluate('window.scrollTo(0,0)')
 page.screenshot(path='/home/isaac/vault/argand/prototype/evidence/evaluate-anytime-browser.png',full_page=True)
 page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 print('PASS: active-voice evaluation, uncertain dots, snapshot replacement, automatic completion evaluation, mobile width. Voice/evaluator/completion simulated; persistence real.',flush=True)
 b.close()
