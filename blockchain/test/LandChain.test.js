import { expect } from "chai";
import { network } from "hardhat";
describe("LandChain", function () {
  async function setup() { const { ethers } = await network.create(); const [owner, next, other] = await ethers.getSigners(); const C = await ethers.getContractFactory("LandChain"); const c = await C.deploy(); return { c, owner, next, other, ethers }; }
  it("registers and looks up a property", async function () { const { c, owner } = await setup(); await expect(c.registerProperty(1001, "REF-1", "sha256:abc")).to.emit(c, "PropertyRegistered"); const p = await c.getProperty(1001); expect(p.owner).to.equal(owner.address); expect(p.exists).to.equal(true); expect(await c.getOwner(1001)).to.equal(owner.address); });
  it("rejects duplicate registration", async function () { const { c } = await setup(); await c.registerProperty(1, "R", "H"); await expect(c.registerProperty(1, "R", "H")).to.be.revertedWith("Property already exists"); });
  it("verifies existing properties", async function () { const { c } = await setup(); await expect(c.verifyProperty(1)).to.be.revertedWith("Property does not exist"); await c.registerProperty(1, "R", "H"); await c.verifyProperty(1); expect(await c.isVerified(1)).to.equal(true); });
  it("allows only the owner to transfer and rejects zero address", async function () { const { c, next, other, ethers } = await setup(); await c.registerProperty(1, "R", "H"); await expect(c.connect(other).transferOwnership(1, next.address)).to.be.revertedWith("Only owner can transfer"); await expect(c.transferOwnership(1, ethers.ZeroAddress)).to.be.revertedWith("Invalid new owner"); await expect(c.transferOwnership(1, next.address)).to.emit(c, "OwnershipTransferred"); expect(await c.getOwner(1)).to.equal(next.address); });
});
