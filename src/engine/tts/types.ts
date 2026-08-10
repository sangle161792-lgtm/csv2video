export interface TTSInput {id:string;text:string;speaker:string;outputPath:string;voice?:string}
export interface TTSResult {audioPath:string;duration?:number;provider:string;voice:string}
export interface TTSProvider {readonly id:string;synthesize(input:TTSInput):Promise<TTSResult>}
