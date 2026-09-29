# LandChain Real Estate Tokenization Platform

A clean, self-contained local MVP that records property registration and ownership on an EVM chain, keeps application metadata in PostgreSQL, and deploys one whole-share ERC-20 contract per verified property.

> **Development only.** This MVP uses a local Hardhat chain and an environment-configured relayer key. It has no production identity, custody, legal-title, document-storage, or audit controls. Do not use the demo keys or deploy this design with real property, funds, or production credentials.

## Architecture

```text
Next.js dashboard (localhost:3000)
          │ HTTP / JSON
          ▼
FastAPI API (localhost:8000) ───── PostgreSQL (landchain)
          │ Web3.py / configured backend signer
          ▼
Hardhat JSON-RPC (localhost:8545)
          ├── LandChain registry
          └── PropertyToken ERC-20 contracts
```

For blockchain writes, the API waits for a successful transaction receipt before committing the corresponding PostgreSQL state. Property inspection reads the current chain and reports field-level mismatches. Token balances are read from their deployed contracts. The local demo relayer supports one configured signer at a time; property registration and property/token transfer require that signer to hold the relevant ownership or tokens.

## Folder structure

- `blockchain/` — Solidity contracts, Hardhat configuration, deployment script, and contract tests.
- `backend/` — FastAPI application, SQLAlchemy models, Web3 services, seed script, and API tests.
- `frontend/` — responsive Next.js dashboard and API client.
- `.env.example` — environment-variable template. The root `.env` and `backend/.env` are ignored by Git.

## Prerequisites

- Windows 10/11 with Node.js 20.9+ and npm.
- Python 3.12+ (the bundled Codex Python is suitable for local validation, but a normal Python install is recommended for daily development).
- PostgreSQL 15+ running locally; the PostgreSQL command-line tools are useful for setup/reset.
- PowerShell.

## Configure environment

Copy `.env.example` to `backend/.env`. The backend loads `.env` from its working directory. Keep `BLOCKCHAIN_PRIVATE_KEY` only in this backend file and do not commit it. Start a local Hardhat node and copy the private key for its first development account from the node's own console into `BLOCKCHAIN_PRIVATE_KEY`; this key is public demo material and must never be reused elsewhere.

Set the PostgreSQL values in `backend/.env`. Create the development database once, for example from an administrative `psql` prompt:

```sql
CREATE DATABASE landchain;
```

`LANDCHAIN_CONTRACT_ADDRESS` is filled after deployment. The frontend only uses `NEXT_PUBLIC_API_URL`; it never receives the private key.

Example backend `.env` (replace credentials and key locally):

```dotenv
BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545
LANDCHAIN_CONTRACT_ADDRESS=
BLOCKCHAIN_PRIVATE_KEY=
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-local-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=landchain
```

## Start the blockchain

In PowerShell window 1:

```powershell
cd blockchain
npm install
npx hardhat node
```

Keep the node window open. Hardhat prints development accounts and their private keys for local use only.

## Deploy LandChain

In PowerShell window 2:

```powershell
cd blockchain
npx hardhat compile
npx hardhat run scripts/deploy.js --network localhost
```

The deployed address and transaction hash are written to `blockchain/deployments/localhost.json`. Copy the printed `LANDCHAIN_CONTRACT_ADDRESS` value into `backend/.env`. The deployer key configured in the backend must correspond to the account that owns properties it registers/transfers and the token shares it sends. Deployments are checked against the previous saved local address to avoid reusing it after a chain reset.

The Hardhat project uses the current ESM-based Hardhat setup. If your Windows account policy blocks Hardhat from writing its global config under AppData, set task-local paths before running it:

```powershell
$env:APPDATA = "$PWD\.hardhat-appdata"
$env:LOCALAPPDATA = "$PWD\.hardhat-localdata"
```

For an alternate local RPC port, set `$env:LOCALHOST_RPC_URL` before invoking the deployment command; the default is still `http://127.0.0.1:8545`.

## Start the backend

In PowerShell window 3 (from the repository root):

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API: <http://127.0.0.1:8000>  
Swagger: <http://127.0.0.1:8000/docs>  
Health: <http://127.0.0.1:8000/api/health>

The MVP creates SQLAlchemy tables at startup. For a persistent production system, add reviewed schema migrations before deployment.

## Start the frontend

In PowerShell window 4:

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000>. To use a different API URL, set `NEXT_PUBLIC_API_URL` in the frontend environment before starting Next.js.

## Tests and build

```powershell
cd blockchain
npm install
npx hardhat compile
npx hardhat test
```

```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt
python -m pytest
```

```powershell
cd frontend
npm install
npm run build
```

## Development seed

With PostgreSQL, Hardhat, the deployed contract, and the backend environment configured, run from `backend`:

```powershell
venv\Scripts\activate
python scripts\seed_dev.py
```

It creates three demo users from the first three local Hardhat account addresses, registers properties 1002 and 1003 by sending real local-chain transactions, verifies them, deploys a real token contract for property 1002, and transfers 100 shares to the second demo account. The script is idempotent for its sample records on the current database and chain.

## Development reset (destructive)

**DEVELOPMENT ONLY:** `backend\scripts\reset-dev.ps1` drops and recreates the configured database, stops the process listening on local port 8545, starts a new Hardhat node, deploys a new LandChain address, updates `backend/.env`, and seeds new demo data. It destroys all data in the configured PostgreSQL database and restarts the local node; verify the `.env` points only to a disposable development database before running it.

Run from PowerShell after installing blockchain/backend dependencies and configuring `backend/.env`:

```powershell
cd backend
.\scripts\reset-dev.ps1
```

## Public test demo (Render + Neon + Sepolia)

This is a public demonstration on Ethereum's Sepolia test network. It does not represent real property title or real money. The Render blueprint in `render.yaml` creates the Next.js and FastAPI web services; Neon supplies PostgreSQL. Render's free web services sleep after inactivity, so the first visit may take about a minute. Neon's free plan currently includes 0.5 GB per project and 100 compute-hours per month. Render's free Postgres databases expire after 30 days, so this setup uses Neon instead. Check each provider's current limits before deploying: [Render free instance limits](https://render.com/docs/free), [Neon free plan limits](https://neon.com/docs/introduction/plans).

The API is public and has no user authentication. It limits write requests to 20 per minute per client, but that is only an abuse guard. Use a freshly generated Sepolia-only wallet, fund it with only a small amount of test ETH, and never put real funds or real property documents in this demo.

### 1. Create a dedicated test wallet

From PowerShell:

```powershell
cd C:\Users\Sanjay\Landchain-MVP\blockchain
npm run wallet:sepolia-demo
```

The command prints the public address and saves the private key only to `blockchain/.local-sepolia-wallet.json`. That file is ignored by Git. Keep a secure backup; the command refuses to overwrite it. Use a Sepolia faucet to request test ETH for the public address.

### 2. Get a Sepolia RPC URL

Create an Ethereum Sepolia app with an RPC provider such as [Alchemy](https://www.alchemy.com/). Keep its endpoint private because the URL contains your API key. Do not paste it into GitHub or this chat.

### 3. Deploy LandChain to Sepolia

Set the RPC endpoint and the dedicated wallet key in the current PowerShell session, then deploy:

```powershell
$env:SEPOLIA_RPC_URL = "https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY"
$env:BLOCKCHAIN_PRIVATE_KEY = "YOUR_DEMO_WALLET_PRIVATE_KEY"
npm run deploy:sepolia
Remove-Item Env:\SEPOLIA_RPC_URL
Remove-Item Env:\BLOCKCHAIN_PRIVATE_KEY
```

Run this from `blockchain/`. The script prints the deployed contract address and writes the full deployment record under the ignored `blockchain/deployments/sepolia.json` file. Do not deploy with the standard Hardhat test account or a personal wallet.

### 4. Create the cloud database

Create a new PostgreSQL project on [Neon](https://neon.com/), then copy its connection string. Keep the database project separate from any existing `landchain` database. The Render service converts the standard `postgresql://` connection string to the psycopg v3 driver format at runtime.

### 5. Provision the web services

1. Create a Render account and connect the GitHub repository `Sanjay-6688/landchaimvp`.
2. In Render, create a new Blueprint using the repository's `main` branch and `render.yaml`.
3. In the Blueprint's secret prompts, provide:
   - `DATABASE_URL`: the Neon connection string.
   - `BLOCKCHAIN_RPC_URL`: the same Sepolia RPC endpoint used to deploy.
   - `BLOCKCHAIN_PRIVATE_KEY`: the dedicated test wallet key from the local ignored wallet file.
   - `LANDCHAIN_CONTRACT_ADDRESS`: the Sepolia contract address printed by the deploy command.
4. Deploy the Blueprint. Render connects the frontend URL to the API URL automatically. Wait for both services to report healthy, then open the Render URL for `landchain-demo-web`.

The blueprint uses free Render web services, which sleep after 15 minutes without traffic and can take about a minute to wake. Neon free projects have monthly usage limits; monitor usage in its dashboard. Public demo operations spend Sepolia test ETH and are not access-controlled, so keep the wallet balance low.

## API outline

- `GET /api/health`
- `POST`, `GET /api/users`
- `POST /api/properties/register`; `GET /api/properties`; `GET /api/properties/{id}`
- `GET /api/properties/{id}/inspect`
- `POST /api/properties/{id}/verify`
- `POST /api/properties/{id}/transfer`
- `POST /api/properties/{id}/tokenize`
- `GET /api/tokens/{id}/balance?wallet=0x...`
- `POST /api/tokens/{id}/transfer`

## Troubleshooting

- **Blockchain unavailable:** keep `npx hardhat node` running and check `BLOCKCHAIN_RPC_URL`.
- **Contract not configured:** deploy to `localhost` and update `LANDCHAIN_CONTRACT_ADDRESS` in `backend/.env`.
- **Signer does not own property:** set the backend signer key to the current owner's local Hardhat account. For token transfers, it must be the sender with enough shares.
- **Property exists in database but not on current chain:** the API inspection endpoint reports this explicitly; after a chain reset, run the development reset to rebuild demo state.
- **PostgreSQL unavailable:** verify the PostgreSQL service, database name, port, user, password, and that the database exists.
- **Token artifact missing:** compile contracts from `blockchain` before starting property tokenization.
- **Windows blocks Hardhat's global config directory:** set the task-local `APPDATA` and `LOCALAPPDATA` values shown in the deploy section, then rerun the Hardhat command.
- **CORS/API errors:** use the documented localhost ports and confirm the API is listening at `NEXT_PUBLIC_API_URL`.

## Limitations

The application has no authentication or per-user authorization. Any local API caller can request operations available to the configured backend signer. PostgreSQL and EVM writes cannot be committed atomically; if PostgreSQL fails after chain confirmation, the API reports that the chain succeeded and the database synchronization failed so an operator can reconcile it. The property registration flow checks the signer against the selected user's wallet; changing signer requires restarting the backend. This is a local MVP, not a title registry or production token issuance system.

## Full local E2E flow

For a clean property ID 1001, first run the development reset, then start FastAPI and run:

```powershell
cd backend
venv\Scripts\activate
python scripts\e2e_local.py
```

This script requires PostgreSQL (it refuses SQLite), uses the configured local Hardhat accounts, and performs property registration, verification, ownership transfer, token deployment, a 100-share transfer, and the final consistency check through the HTTP API.
