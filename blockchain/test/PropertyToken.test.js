import { expect } from "chai";
import { network } from "hardhat";
describe("PropertyToken", function () {
  it("mints whole shares to the deployer and supports transfers", async function () { const { ethers } = await network.create(); const [owner, recipient] = await ethers.getSigners(); const T = await ethers.getContractFactory("PropertyToken"); const t = await T.deploy("Property 1001", "P1001", 1000); expect(await t.totalSupply()).to.equal(1000); expect(await t.balanceOf(owner.address)).to.equal(1000); expect(await t.decimals()).to.equal(0); await t.transfer(recipient.address, 100); expect(await t.balanceOf(recipient.address)).to.equal(100); });
  it("rejects transfers with insufficient balance", async function () { const { ethers } = await network.create(); const [, recipient] = await ethers.getSigners(); const T = await ethers.getContractFactory("PropertyToken"); const t = await T.deploy("Shares", "SHR", 10); await expect(t.transfer(recipient.address, 11)).to.be.revertedWithCustomError(t, "ERC20InsufficientBalance"); });
});
