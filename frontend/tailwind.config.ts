import type { Config } from "tailwindcss";
const config: Config={content:["./app/**/*.{ts,tsx}","./components/**/*.{ts,tsx}"],theme:{extend:{colors:{ink:"#080b18",panel:"#10162a",accent:"#8b7cff"},boxShadow:{glow:"0 0 40px rgba(124,108,255,.14)"}}},plugins:[]};export default config;
