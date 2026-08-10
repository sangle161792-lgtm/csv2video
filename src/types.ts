export type ActionType='idle'|'blink'|'look_up'|'jump'|'talk'|'proud'|'surprised'|'enter'|'exit';
export interface Dialogue {id:string;speaker:string;text:string;audio?:string;after?:string;gap?:number}
export interface Action {type:ActionType;start?:string;end?:string;at?:number;duration?:number}
export interface Shot {id:string;duration:number|'auto';camera:{shot:'wide'|'medium'|'close';movement?:{type:'static'|'pan'|'tilt'|'push_in'|'pull_out'|'follow'|'shake';intensity?:'subtle'|'normal'}};environment:string;dialogue?:Dialogue;actions?:Action[];transition?:'fade'|'wipe'}
export interface Episode {episode:{id:string;title:string;fps:number;width:number;height:number};shots:Shot[]}
export interface TimedDialogue extends Dialogue {start:number;end:number;duration:number;shotId:string}
export interface CompiledShot extends Shot {start:number;end:number;duration:number}
export interface Timeline {episode:Episode['episode'];duration:number;shots:CompiledShot[];dialogues:Record<string,TimedDialogue>;subtitles:Array<{id:string,start:number;end:number,text:string;speaker:string}>;lipSync:Record<string,Array<{time:number;state:'closed'|'small'|'medium'|'wide'}>>}
