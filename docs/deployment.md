# Deployment guide

## Recommended first deployment: Render demo

1. Push this project to your GitHub repository.
2. Sign in to https://dashboard.render.com and choose **New > Blueprint**.
3. Connect the repository and select its branch. Render reads `render.yaml`.
4. Review the free Docker web service and deploy. It runs in demo mode, without a Kafka broker.
5. Wait until the service is live; open its generated HTTPS URL.
6. Copy `API_KEY` from the service's environment settings. In DeepSOC, select **API access** and enter it. Do not put secrets in Git.
7. Check `/health`, simulate a threat, open the alert, update its incident and simulate a block.

Free service storage is ephemeral, and the service may spin down when idle. For durable data, select a service plan supporting disks, attach a disk at `/data`, and retain `DB_PATH=/data/soc.db`. The supplied blueprint intentionally does not provision a paid disk.

Official references: https://render.com/docs/deploy-fastapi and https://render.com/docs/blueprint-spec .

## Full Kafka deployment on one Linux server

Install Docker Engine and the Compose plugin from Docker's official instructions. Clone your repository onto the server. Create a `.env` with a strong random `API_KEY`, then run:

```sh
docker compose up --build -d
docker compose ps
docker compose logs --tail=100 api worker
```

The API listens on host loopback port 8000. Expose it through an HTTPS reverse proxy configured for your domain. Kafka's host port is also bound to loopback; the API and worker communicate through Docker's internal Kafka listener. Do not expose the broker's plaintext listener on the public internet. Back up the `soc-data` volume regularly.

This Compose file runs one broker and one worker on one host. It provides a usable portfolio stack, not broker replication, a scalable distributed database, TLS/SASL Kafka authentication, fine-grained user roles or production incident-response integrations. Health checks verify the API/broker, not consumer progress. Monitor worker logs and ingestion/processing lag before treating it as an operational SOC.

## Git handoff

The project includes a `.gitignore` for environments, database/WAL files and generated artifacts. Commit source and deployment files; never commit API keys or log databases. Push a reviewed branch and merge it into the branch selected by Render. Automatic deploys then follow that branch.
