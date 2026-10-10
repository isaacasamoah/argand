import {useSyncExternalStore} from 'react';
export const chapters=[
 {title:'Representing complex numbers',body:'A real number can be represented on a number line. To represent a complex number, we use two axes. A complex number has the form z = a + bi, where a and b are real numbers and i² = −1.\nThe real part, a, gives the horizontal coordinate; the imaginary part, b, gives the vertical coordinate. For example, 1 + i corresponds to (1, 1). Follow the dashed lines, then use the sliders to explore other points.',label:'Move the sliders: negative values take you left or down'},
 {title:'Modulus and argument',body:'We can also describe a complex number by its distance from the origin and its angle from the positive real axis. For 1 + i, the green line gives the modulus: |z| = √(1² + 1²) = √2 ≈ 1.41.\nThe amber arc gives the argument, θ = 45°, measured anticlockwise from the positive real axis. These two quantities describe the number in polar form: z = r(cos θ + i sin θ), where r is the modulus.',label:'Green line: distance √2 · amber arc: angle 45°'},
 {title:'Powers and roots',body:'To square a complex number, square its modulus and double its argument. For 1 + i, the modulus becomes (√2)² = 2 and the argument becomes 90°. The resulting point represents 2i.\nFor −1 − i, doubling 225° gives 450°, equivalent to 90°. It also squares to 2i. Select each root and compare. To find a cube, cube the modulus and triple the argument.',label:'Choose each starting point and square it: both reach 2i'},
 {title:'Application: alternating voltage',body:'In an alternating-current (AC) circuit, voltage varies periodically. A complex number can represent the amplitude (peak voltage) and phase (starting position in the cycle). Here, the modulus represents amplitude and the argument represents phase.\nAs the arrow rotates, its horizontal component gives the voltage at that instant. Compare 1 and i: both have amplitude 1 V, but their phases differ by 90°, or a quarter-cycle. Move the slider to see how the arrow corresponds to the voltage graph.',label:'Same wave size, different timing'}
];

type State={revision:number,step:number,real:number,imag:number,root:number,squared:boolean,phase:number,time:number};
let state:State={revision:0,step:0,real:1,imag:1,root:0,squared:false,phase:0,time:0};
const listeners=new Set<()=>void>();
export function useLessonState(){return useSyncExternalStore(fn=>{listeners.add(fn);return()=>{listeners.delete(fn)}},()=>state)}
export function updateLesson(patch:Partial<Omit<State,'revision'>>){state={...state,...patch,revision:state.revision+1};listeners.forEach(fn=>fn());return lessonSnapshot()}
export function lessonSnapshot(){
 const {revision,step,real,imag,root,squared,phase,time}=state;
 const chapter=chapters[step];
 const controls=step===0?{real,imag}:step===2?{root,squared}:step===3?{phase,time}:{};
 const point=step===0?[real,imag]:step===1?[1,1]:step===2?(squared?[0,2]:root===0?[1,1]:[-1,-1]):[Math.cos((time+phase)*Math.PI/180),Math.sin((time+phase)*Math.PI/180)];
 return {mode:'lesson',revision,stage:step+1,title:chapter.title,explanation:chapter.body,controls,diagram:step===3?{phasor:phase===0?'1':'i',amplitudeVolts:1,voltage:point[0],point}: {point},allowedUpdates:step===0?['real','imag']:step===2?['root','squared']:step===3?['phase','time']:[]};
}
export function applyDiagramUpdate(args:Record<string,unknown>){
 const before=lessonSnapshot();
 if(args.revision!==state.revision)return {status:'stale_state',state:before};
 const patch:Partial<State>={};
 for(const [key,value] of Object.entries(args)){
  if(key==='revision'||value===null)continue;
  if(!before.allowedUpdates.includes(key))return {status:'invalid_control',state:before};
  if(key==='squared'){if(typeof value!=='boolean')return {status:'invalid_value',state:before};patch.squared=value;continue;}
  if(typeof value!=='number'||!Number.isFinite(value))return {status:'invalid_value',state:before};
  if(key==='real'||key==='imag'){if(value< -2||value>2)return {status:'out_of_range',state:before};patch[key]=Math.round(value*10)/10;}
  if(key==='root'){if(value!==0&&value!==1)return {status:'out_of_range',state:before};patch.root=value;patch.squared=false;}
  if(key==='phase'){if(value!==0&&value!==90)return {status:'out_of_range',state:before};patch.phase=value;}
  if(key==='time'){if(value<0||value>360||value%5!==0)return {status:'out_of_range',state:before};patch.time=value;}
 }
 if(typeof args.squared==='boolean')patch.squared=args.squared;
 return {status:'applied',state:updateLesson(patch)};
}
