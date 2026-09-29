import { network } from "hardhat";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

async function main() {
  const { ethers } = await network.create();
  const [deployer] = await ethers.getSigners();
  const LandChain = await ethers.getContractFactory("LandChain");
  const root = path.dirname(fileURLToPath(import.meta.url));
  const file = path.join(root, "..", "deployments", "localhost.json");
  let previousAddress = null;
  if (fs.existsSync(file)) { try { previousAddress = JSON.parse(fs.readFileSync(file, "utf8")).address?.toLowerCase() || null; } catch {} }
  let contract = await LandChain.deploy();
  await contract.waitForDeployment();
  let address = await contract.getAddress();
  // A restarted local node resets account nonces; advance it if that would reuse
  // the last saved deployment address, so repeated local deploys remain distinct.
  while (previousAddress && address.toLowerCase() === previousAddress) {
    const nonce = await ethers.provider.getTransactionCount(deployer.address);
    await (await deployer.sendTransaction({ to: deployer.address, value: 0 })).wait();
    contract = await LandChain.deploy();
    await contract.waitForDeployment();
    address = await contract.getAddress();
    if (nonce > 100) throw new Error("Could not advance to a fresh deployment address");
  }
  const info = { network: "localhost", chainId: Number((await ethers.provider.getNetwork()).chainId), address, deployer: deployer.address, transactionHash: contract.deploymentTransaction().hash, deployedAt: new Date().toISOString() };
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(info, null, 2));
  console.log(`LandChain deployed: ${address}`);
  console.log(`Deployment information saved: ${file}`);
  console.log(`Set LANDCHAIN_CONTRACT_ADDRESS=${address} in backend/.env`);
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
