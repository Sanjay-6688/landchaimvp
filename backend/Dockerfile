FROM node:22-bookworm-slim AS contracts

WORKDIR /workspace
COPY blockchain/package.json blockchain/package-lock.json ./blockchain/
RUN cd blockchain && npm ci
COPY blockchain/hardhat.config.js ./blockchain/
COPY blockchain/contracts ./blockchain/contracts
RUN cd blockchain && npx hardhat compile

FROM python:3.12-slim

WORKDIR /app
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY backend/ /app/backend/
COPY --from=contracts /workspace/blockchain/artifacts /app/blockchain/artifacts

WORKDIR /app/backend
EXPOSE 10000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
