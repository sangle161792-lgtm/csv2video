export const secondsToFrames=(seconds:number,fps:number)=>Math.round(seconds*fps);
export const srtTime=(s:number)=>{const ms=Math.round(s*1000);const h=Math.floor(ms/3600000),m=Math.floor(ms%3600000/60000),sec=Math.floor(ms%60000/1000),n=ms%1000;return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')},${String(n).padStart(3,'0')}`};
