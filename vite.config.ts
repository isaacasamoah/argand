import {defineConfig} from 'vite';
import {readdirSync,readFileSync} from 'node:fs';
export default defineConfig({plugins:[{name:'local-math-fonts',generateBundle(){for(const name of readdirSync('node_modules/mathlive/fonts'))this.emitFile({type:'asset',fileName:`mathlive-fonts/${name}`,source:readFileSync(`node_modules/mathlive/fonts/${name}`)})}}]});
