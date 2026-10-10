from playwright.sync_api import sync_playwright
import json
with sync_playwright() as p:
 b=p.chromium.launch();page=b.new_page(viewport={'width':1280,'height':720})
 page.add_init_script('''window.sent=[];window.pc=null;class FakePeer{iceGatheringState='complete';localDescription=null;constructor(){window.pc=this}createDataChannel(){const c={readyState:'open',send:s=>window.sent.push(JSON.parse(s)),close(){this.readyState='closed'}};this.channel=c;return c}async createOffer(){return {type:'offer',sdp:'fake'}}async setLocalDescription(s){this.localDescription=s}async setRemoteDescription(){this.channel.onmessage({data:JSON.stringify({type:'session.started'})})}addTrack(){}close(){}}window.RTCPeerConnection=FakePeer;navigator.mediaDevices.getUserMedia=async()=>new MediaStream();window.emit=e=>window.pc.channel.onmessage({data:JSON.stringify(e)});''')
 page.route('**/api/voice/session',lambda route:route.fulfill(json={'session':{'id':'fixture'},'transport':{'sdp':'fake'}}))
 page.goto('http://127.0.0.1:18770');page.get_by_role('button',name='Talk it through',exact=True).click();page.get_by_role('button',name='End conversation',exact=True).wait_for()
 def call(name,args,id):
  page.evaluate('''([name,args,id])=>{emit({type:'response.event',delegation_id:id,event:{type:'response.output_item.done',item:{type:'function_call',name,arguments:JSON.stringify(args),call_id:id}}});emit({type:'response.event',delegation_id:id,event:{type:'response.completed'}})}''',[name,args,id])
  page.wait_for_function('(id)=>sent.some(e=>e.item?.call_id===id)',arg=id)
  return json.loads(page.evaluate('(id)=>sent.find(e=>e.item?.call_id===id).item.output',id))
 state=call('read_lesson_state',{},'read1');assert state['stage']==1
 r=call('update_diagram',{'revision':state['revision'],'real':-1.5,'imag':-0.5},'update1');assert r['status']=='applied'
 assert page.get_by_label('Real part',exact=True).input_value()=='-1.5'
 assert page.get_by_label('Imaginary coefficient',exact=True).input_value()=='-0.5'
 assert page.locator('.lesson-diagram').get_attribute('aria-label')=='Complex plane: real -1.5, imaginary -0.5'
 stale=call('update_diagram',{'revision':state['revision'],'real':2},'stale');assert stale['status']=='stale_state'
 page.get_by_role('button',name='Next',exact=True).click();state=call('read_lesson_state',{},'read2');assert state['stage']==2
 assert call('update_diagram',{'revision':state['revision'],'real':2},'invalid')['status']=='invalid_control'
 r=call('update_diagram',{'revision':state['revision'],'modulus':2,'angle':90},'polar');assert r['state']['diagram']['point']==[0,2]
 assert page.get_by_label('Modulus',exact=True).input_value()=='2'
 assert page.get_by_label('Angle',exact=True).input_value()=='90'
 assert page.locator('.lesson-diagram').get_attribute('aria-label')=='Complex plane: real 0, imaginary 2'
 assert call('update_diagram',{'revision':r['state']['revision'],'angle':365},'badangle')['status']=='out_of_range'
 page.get_by_label('Angle',exact=True).fill('180');state=call('read_lesson_state',{},'slider');assert state['diagram']['point']==[-2,0]
 r=call('update_diagram',{'revision':state['revision'],'modulus':0},'origin');assert r['state']['diagram']['point']==[0,0]
 assert page.get_by_text('At the origin, the argument is undefined.').is_visible()
 page.get_by_role('button',name='Next',exact=True).click();state=call('read_lesson_state',{},'read3');assert call('update_diagram',{'revision':state['revision'],'root':1,'squared':True},'root')['state']['diagram']['point']==[0,2]
 page.get_by_role('button',name='Next',exact=True).click();state=call('read_lesson_state',{},'read4');assert call('update_diagram',{'revision':state['revision'],'phase':90,'time':180},'wave')['status']=='applied'
 assert page.get_by_label('Wave time',exact=True).input_value()=='180'
 page.wait_for_timeout(250)
 pair=page.evaluate('''()=>{const a=sent.filter(e=>e.type==='session.thinking.append').at(-1).content;const b=sent.filter(e=>e.type==='response.item.create'&&e.item.role==='developer').at(-1).item.content[0].text;return [JSON.parse(a),JSON.parse(b.slice(b.indexOf('{')))]}''');assert pair[0]==pair[1]
 page.get_by_role('button',name='Try it yourself').click();state=call('read_lesson_state',{},'practice');assert state['mode']=='practice'
 assert call('update_diagram',{'revision':0,'real':0},'denied')['status']=='not_in_lesson'
 page.get_by_label('Candidate modulus').fill('2');page.get_by_label('Candidate angle').fill('120');page.get_by_role('button',name='Cube this point').click();page.get_by_text('Matches the target.',exact=False).wait_for()
 page.wait_for_timeout(300)
 pair=page.evaluate("""()=>{const a=sent.filter(e=>e.type==='session.thinking.append').at(-1).content;const b=sent.filter(e=>e.type==='response.item.create'&&e.item.role==='developer').at(-1).item.content[0].text;return [JSON.parse(a),JSON.parse(b.slice(b.indexOf('{')))]}""")
 assert pair[0]==pair[1]
 assert pair[0]['exploration']['controls']=={'modulus':2,'angle':120}
 assert pair[0]['exploration']['checker']['matches'] is True
 assert pair[0]['exploration']['cubed']==[8,0]

 print('PASS: tools visibly change coordinates, roots and wave; reject stale/wrong-stage edits; detect navigation and practice; identical state sent to both models.')
 page.evaluate("emit({type:'session.closed',reason:'close_requested'})");b.close()
