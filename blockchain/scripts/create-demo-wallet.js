import { Wallet } from "ethers";
import { existsSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const output = path.join(root, "..", ".local-sepolia-wallet.json");

if (existsSync(output)) {
  throw new Error(`Wallet file already exists; refusing to overwrite it: ${output}`);
}

const wallet = Wallet.createRandom();
writeFileSync(output, `${JSON.stringify({ address: wallet.address, privateKey: wallet.privateKey }, null, 2)}\n`, { mode: 0o600 });
console.log(`Created a Sepolia-only demo wallet. Public address: ${wallet.address}`);
console.log(`Private key saved locally in ${output}; it was not printed. Do not commit or reuse it.`);
