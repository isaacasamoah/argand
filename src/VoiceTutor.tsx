import {useEffect,useRef,useState} from 'react';
import {Mic,Square} from 'lucide-react';
type Props={available:boolean,problemId:string,lesson:boolean,context:string,parentId?:string};
export function VoiceTutor(props:Props){
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
   channel.onmessage=({data})=>{if(active.current!==c)return;let e;try{e=JSON.parse(data)}catch{return}
    if(e.type==='session.started'){clearTimeout(c.timer);setState('live');setStatus('Microphone on · talk naturally');sendContext();channel.send(JSON.stringify({type:'session.instructions.append',delegation_id:null,content:latest.current.lesson?'Begin now in English. Offer to walk through the visible lesson on complex numbers. Start with the real and imaginary axes, then pause for a question. Use the backend for the explanation.':'Greet the learner briefly in English and ask whether they have a question or want to try the problem. Then listen.'}));}
    if(e.type==='session.closed'){cleanup();setState('idle');setStatus('Voice conversation ended.');}
    if(e.type==='error'){setStatus('The voice service reported an error. End voice and retry.');}
    if((e.type==='session.input_transcript.delta'||e.type==='session.output_transcript.delta')&&typeof e.delta==='string'){const who=e.type.includes('input')?'You':'Tutor';setTranscript(old=>{const next=[...old];if(next.at(-1)?.who===who)next[next.length-1]={who,text:next[next.length-1].text+e.delta};else next.push({who,text:e.delta});return next.slice(-40)});}
   };
   channel.onclose=()=>{if(active.current===c){cleanup();setState('idle');setStatus('Disconnected; session finalization was not confirmed.')}};
   c.stream=await navigator.mediaDevices.getUserMedia({audio:true});if(active.current!==c){c.stream.getTracks().forEach(t=>t.stop());return}c.stream.getTracks().forEach(t=>peer.addTrack(t,c.stream!));
   await peer.setLocalDescription(await peer.createOffer());
   if(peer.iceGatheringState!=='complete')await new Promise<void>((resolve,reject)=>{const timer=setTimeout(()=>{peer.removeEventListener('icegatheringstatechange',check);reject(new Error('Network setup timed out.'))},10000);function check(){if(peer.iceGatheringState==='complete'){clearTimeout(timer);peer.removeEventListener('icegatheringstatechange',check);resolve()}}peer.addEventListener('icegatheringstatechange',check);check()});
   const r=await fetch('/api/voice/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sdp:peer.localDescription?.sdp,problem_id:props.problemId,lesson:props.lesson,parent_id:props.parentId}),signal:AbortSignal.timeout(45000)});const result=await r.json();if(!r.ok)throw new Error(result.detail||'Voice could not connect.');if(active.current!==c)return;
   await peer.setRemoteDescription({type:'answer',sdp:result.transport.sdp});
  }catch(e){cleanup();setState('idle');setStatus(e instanceof Error?e.message:'Voice could not connect.')}
 }
 function stop(){const c=active.current;if(!c)return;setState('closing');setStatus('Ending voice…');c.stream?.getTracks().forEach(t=>t.enabled=false);if(c.channel.readyState==='open')c.channel.send(JSON.stringify({type:'session.close'}));c.timer=setTimeout(()=>{cleanup();setState('idle');setStatus('Microphone stopped; session finalization unconfirmed.')},15000)}
 return <section className="voice-tutor"><div><b>Talk it through</b><p>{status|| (props.available?'A voice tutor for the lesson and your questions.':'Voice is ready to connect once the OpenAI key is configured.')}</p></div>{state==='idle'?<button className="primary" disabled={!props.available} onClick={start}><Mic size={17}/>{props.lesson?'Talk me through the lesson':'Talk to the tutor'}</button>:<button className="outline" disabled={state!=='live'} onClick={stop}><Square size={15}/>{state==='connecting'?'Connecting…':state==='closing'?'Ending…':'End voice'}</button>}<audio ref={audio} autoPlay controls hidden={state==='idle'}/>{transcript.length>0&&<details><summary>Voice transcript · not evaluated by Jev</summary>{transcript.map((t,i)=><p key={i}><b>{t.who}: </b>{t.text}</p>)}</details>}</section>
}
