export interface EthereumProvider {
  request(args: { method: string; params?: unknown[] | Record<string, unknown> }): Promise<unknown>;
  on?(event: string, listener: (...args: unknown[]) => void): void;
  removeListener?(event: string, listener: (...args: unknown[]) => void): void;
}

declare global {
  interface Window { ethereum?: EthereumProvider }
}

export function ethereumProvider(): EthereumProvider {
  if (typeof window === "undefined" || !window.ethereum) {
    throw new Error("MetaMask was not found. Install or enable the MetaMask browser extension.");
  }
  return window.ethereum;
}

export function encodeTokenBalanceOf(address: string): string {
  return `0x70a08231${address.toLowerCase().replace(/^0x/, "").padStart(64, "0")}`;
}

export function encodeTokenTransfer(recipient: string, amount: bigint): string {
  return `0xa9059cbb${recipient.toLowerCase().replace(/^0x/, "").padStart(64, "0")}${amount.toString(16).padStart(64, "0")}`;
}

export function parseHexInteger(value: unknown): bigint {
  if (typeof value !== "string" || !/^0x[0-9a-f]+$/i.test(value)) {
    throw new Error("Wallet returned an invalid blockchain value.");
  }
  return BigInt(value);
}

export async function switchWalletNetwork(provider: EthereumProvider, chainId: number): Promise<void> {
  await provider.request({ method: "wallet_switchEthereumChain", params: [{ chainId: `0x${chainId.toString(16)}` }] });
}

export async function waitForTransaction(provider: EthereumProvider, hash: string): Promise<void> {
  for (let attempt = 0; attempt < 90; attempt += 1) {
    const receipt = await provider.request({ method: "eth_getTransactionReceipt", params: [hash] }) as { status?: string } | null;
    if (receipt) {
      if (receipt.status !== "0x1") throw new Error("The token transfer was mined but reverted. No tokens were transferred.");
      return;
    }
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  throw new Error(`Transfer is still pending. Check transaction ${hash} on the block explorer.`);
}
