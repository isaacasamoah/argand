import {useEffect,useRef,useState} from 'react';
import {AudioLines,Square} from 'lucide-react';
type Props={available:boolean,problemId:string,lesson:boolean,context:string,parentId?:string};
export function VoiceTutor(props:Props){
 const [voice,setVoice]=useState('quartz');
 const [state,setState]=useState('idle'),[status,setStatus]=useState(''),[transcript,setTranscript]=useState<{who:string,text:string}[]>([]);
 const active=useRef<{peer:RTCPeerConnection,channel:RTCDataChannel,stream?:MediaStream,timer?:ReturnType<typeof setTimeout>}|undefined>(undefined);
 const audio=useRef<HTMLAudioElement>(null),latest=useRef(props);latest.current=props;
 function cleanup(){const c=active.current;active.current=undefined;if(c){clearTimeout(c.timer);c.stream?.getTracks().forEach(t=>t.stop());c.channel.close();c.peer.close();}if(audio.current)audio.current.srcObject=null;}
 function sendContext(){const c=active.current;if(c?.channel.readyState==='open')c.channel.send(JSON.stringify({type:'session.thinking.append',delegation_id:null,content:latest.current.context.slice(0,1800)}));}
 useEffect(()=>{if(state==='live')sendContext()},[props.context,state]);
 useEffect(()=>()=>{const c=active.current;if(c?.channel.readyState==='open')c.channel.send(JSON.stringify({type:'session.close'}));cleanup()},[]);
 async function start(){setState('connecting');setStatus('Connecting microphone…');setTranscript([]);
  try{
   const peer=new RTCPeerConnection(),channel=peer.createDataChannel('oai-events');const c={peer,channel,stream:undefined as MediaStream|undefined,timer:undefined as ReturnType<typeof setTimeout>|undefined};active.current=c;
   c.timer=setTimeout(()=>{if(active.current===c){cleanup();setState('idle');setStatus('Connection timed out. Please try again.')}},60000);
   peer.ontrack=e=>{if(audio.current){audio.current.srcObject=new MediaStream([e.track]);audio.current.play().catch(()=>setStatus('Press play below to hear your tutor.'));}};
   const pending=new Map<string,Promise<{call_id:string,output:string}>[]>();
   channel.onmessage=({data})=>{if(active.current!==c)return;let e;try{e=JSON.parse(data)}catch{return}
    if(e.type==='session.started'){clearTimeout(c.timer);setState('live');setStatus('Microphone on · talk naturally');sendContext();channel.send(JSON.stringify({type:'session.instructions.append',delegation_id:null,content:latest.current.lesson?'Greet briefly in English and ask what the learner would like to explore about the current lesson stage. Do not restart the lesson or repeat concepts unless asked. Delegate maths to the backend, which can call check_roots.':'Greet the learner briefly in English and ask whether they have a question or want to try the problem. Then listen.'}));}
    if(e.type==='response.event'){
     const inner=e.event, id=e.delegation_id;
     if(inner?.type==='response.output_item.done'&&inner.item?.type==='function_call'){
      const item=inner.item;
      const task=(async()=>{try{if(item.name!=='check_roots')throw new Error('Unsupported tool');const args=JSON.parse(item.arguments);const r=await fetch('/api/voice/check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(args)});if(!r.ok)throw new Error('Checker unavailable');const result=await r.json();setTranscript(old=>[...old,{who:'Maths check',text:result.checker.detail}]);return {call_id:item.call_id,output:JSON.stringify(result)}}catch{return {call_id:item.call_id,output:JSON.stringify({status:'not_checked',detail:'The tool could not verify this request.'})}}})();
      pending.set(id,[...(pending.get(id)||[]),task]);
     }
     if(inner?.type==='response.completed'&&pending.has(id)){
      const tasks=pending.get(id)!;pending.delete(id);Promise.all(tasks).then(results=>{if(active.current!==c||channel.readyState!=='open')return;for(const item of results)channel.send(JSON.stringify({type:'response.item.create',item:{type:'function_call_output',...item}}));channel.send(JSON.stringify({type:'response.create'}));});
     }
    }
    if(e.type==='session.closed'){cleanup();setState('idle');setStatus(e.reason==='close_requested'?'Voice conversation ended.':`Voice disconnected (${e.reason||'reason unavailable'}). Start again to reconnect.`);}
    if(e.type==='error'){setStatus(`Voice error: ${e.error?.code||'unknown'}. End voice and retry.`);}
    if((e.type==='session.input_transcript.delta'||e.type==='session.output_transcript.delta')&&typeof e.delta==='string'){const who=e.type.includes('input')?'You':'Tutor';setTranscript(old=>{const next=[...old];if(next.at(-1)?.who===who)next[next.length-1]={who,text:next[next.length-1].text+e.delta};else next.push({who,text:e.delta});return next.slice(-40)});}
   };
   channel.onclose=()=>{if(active.current===c){cleanup();setState('idle');setStatus('Disconnected; session finalization was not confirmed.')}};
   c.stream=await navigator.mediaDevices.getUserMedia({audio:true});if(active.current!==c){c.stream.getTracks().forEach(t=>t.stop());return}c.stream.getTracks().forEach(t=>peer.addTrack(t,c.stream!));
   await peer.setLocalDescription(await peer.createOffer());
   if(peer.iceGatheringState!=='complete')await new Promise<void>((resolve,reject)=>{const timer=setTimeout(()=>{peer.removeEventListener('icegatheringstatechange',check);reject(new Error('Network setup timed out.'))},10000);function check(){if(peer.iceGatheringState==='complete'){clearTimeout(timer);peer.removeEventListener('icegatheringstatechange',check);resolve()}}peer.addEventListener('icegatheringstatechange',check);check()});
   const r=await fetch('/api/voice/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sdp:peer.localDescription?.sdp,problem_id:props.problemId,lesson:props.lesson,parent_id:props.parentId,voice}),signal:AbortSignal.timeout(45000)});const result=await r.json();if(!r.ok)throw new Error(result.detail||'Voice could not connect.');if(active.current!==c)return;
   await peer.setRemoteDescription({type:'answer',sdp:result.transport.sdp});
  }catch(e){cleanup();setState('idle');setStatus(e instanceof Error?e.message:'Voice could not connect.')}
 }
 function stop(){const c=active.current;if(!c)return;setState('closing');setStatus('Ending voice…');c.stream?.getTracks().forEach(t=>t.enabled=false);if(c.channel.readyState==='open')c.channel.send(JSON.stringify({type:'session.close'}));c.timer=setTimeout(()=>{cleanup();setState('idle');setStatus('Microphone stopped; session finalization unconfirmed.')},15000)}
 return <section className="voice-tutor" aria-label="Voice tutor"><div className="voice-controls">{state==='idle'?<button className="voice-icon" title="Talk it through" aria-label="Talk it through" disabled={!props.available} onClick={start}><AudioLines size={21}/></button>:<button className="voice-end" title="Stop the microphone and end the conversation" disabled={state==='closing'} onClick={stop}><Square size={16}/>{state==='connecting'?'Cancel connection':state==='closing'?'Ending…':'End conversation'}</button>}<select aria-label="Tutor voice" title={state==='idle'?'Choose a voice':'End voice to change the speaker'} disabled={state!=='idle'} value={voice} onChange={e=>setVoice(e.target.value)}><option value="quartz">Quartz · Australian</option><option value="ripple">Ripple · Australian</option><option value="vesper">Vesper · British</option><option value="willow">Willow · Irish</option><option value="gleam">Gleam · American</option></select><span role="status">{status||(!props.available?'Voice awaiting API key':'')}</span><audio ref={audio} autoPlay controls hidden={state==='idle'}/></div>{(state!=='idle'||transcript.length>0)&&<details className="voice-conversation" aria-label="Voice conversation"><summary>Transcript</summary>{!transcript.length&&<p>Our conversation will appear here.</p>}{transcript.map((t,i)=><p className={t.who==='You'?'voice-you':''} key={i}><b>{t.who}: </b>{t.text}</p>)}<small>Live transcript · not evaluated by Jev</small></details>}</section>
}
