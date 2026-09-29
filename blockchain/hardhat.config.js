import { defineConfig } from "hardhat/config";
import hardhatToolboxMochaEthers from "@nomicfoundation/hardhat-toolbox-mocha-ethers";

const sepoliaUrl = process.env.SEPOLIA_RPC_URL;
const deployerKey = process.env.BLOCKCHAIN_PRIVATE_KEY;

export default defineConfig({
  plugins: [hardhatToolboxMochaEthers],
  defaultNetwork: "hardhat",
  solidity: { profiles: { default: { version: "0.8.24", settings: { optimizer: { enabled: true, runs: 200 } } } } },
  networks: {
    hardhat: { type: "edr-simulated", chainType: "l1", chainId: 31337 },
    localhost: { type: "http", chainType: "l1", url: process.env.LOCALHOST_RPC_URL || "http://127.0.0.1:8545", chainId: 31337 },
    ...(sepoliaUrl && deployerKey ? {
      sepolia: { type: "http", chainType: "l1", url: sepoliaUrl, chainId: 11155111, accounts: [deployerKey] }
    } : {})
  }
});
