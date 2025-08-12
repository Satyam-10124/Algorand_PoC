Nice — here’s a compact, actionable **1-week PoC spec** you can implement to demo the full SBOM → IPFS → Algorand proof → dashboard flow with *mock* verification (auto or verifier-based). I assume you’ll update the PyTeal contract yourself (you said you can), so I focus on exact endpoints, contract method names, data models, infra, test steps, and a day-by-day plan.

---

# 1-Week PoC Plan — SBOM → IPFS → Algorand Proof (Demo-ready)

## Goal

Ship a demo where: user logs in (wallet), uploads SBOM → stored on IPFS, hash + metadata (control ID + OSCAL framework) recorded on Algorand, verification occurs (auto or via verifier), dashboard shows provable controls.

---

## High-level architecture

* **Frontend (React)**: wallet login (Pera), SBOM upload, metadata form, dashboard.
* **Backend (FastAPI/Flask)**: microservice `/api/compliproof/*` talking to Algorand + IPFS.
* **IPFS**: store SBOM (use Infura/IPFS public node or Pinata).
* **Algorand**: updated PyTeal contract (TestNet), emits logs.
* **Mock Verifier Service**: simple worker that auto-verifies or triggers manual verification.
* **CompliLedger Hook**: simple POST to product endpoint (optional demo).

---

## Contract API (methods to add / update)

Name them clearly to match backend:

1. `register_document`

   * Args: `doc_hash`, `ipfs_cid`, `control_id`, `framework`, `version`, `expiration_ts` (optional)
   * Effects: store metadata, set `status=pending`, `owner=sender`, `attestation_date=now`
   * Emit log: `DOC_REGISTERED:{doc_id}:{ipfs_cid}:{owner}`

2. `assign_verifiers`

   * Args: `doc_id`, `verifier_addresses[]`
   * Effects: store assigned verifiers for doc
   * Emit log: `VERIFIERS_ASSIGNED:{doc_id}`

3. `submit_verification`

   * Args: `doc_id`, `decision` (1 = compliant, 0 = noncompliant), `notes` (optional)
   * Effects: record verifier's vote; compute quorum if assigned, update status (`compliant`/`non-compliant`)
   * Emit log: `VERIFICATION_SUBMITTED:{doc_id}:{verifier}:{decision}`

4. `auto_verify` (optional admin-only)

   * Args: `doc_id`, `decision`
   * Effects: directly set status (useful for demo auto-verify)
   * Emit log: `AUTO_VERIFIED:{doc_id}`

5. `raise_dispute`

   * Args: `doc_id`, `reason`
   * Effects: status -> `under_review`; emit `DISPUTE_RAISED`

6. `view_status` (read-only)

   * returns full doc metadata, assigned verifiers, decision history

**Notes**: store minimal arrays/maps due to TEAL state limits — keep per-doc small (or store heavy history off-chain & index via logs).

---

## Backend API Spec (example JSON)

Base: `POST /api/compliproof/*` — all JSON; auth via simple API key for demo.

### 1) `POST /api/compliproof/upload`

* Purpose: receive SBOM file, pin to IPFS, return `ipfs_cid` + `sha256`
* Request: multipart/form-data `file`
* Response:

```json
{
  "ipfs_cid": "bafy...",
  "sha256": "a1b2c3...",
  "size": 12345
}
```

### 2) `POST /api/compliproof/register`

* Purpose: register doc on Algorand
* Request:

```json
{
  "doc_hash": "a1b2c3...",
  "ipfs_cid": "bafy...",
  "control_id": "AC-2",
  "framework": "OSCAL-NIST-800-53",
  "version": "1.0",
  "expiration_ts": 1735689600
}
```

* Response:

```json
{
  "status": "submitted",
  "txn_id": "XYZ...",
  "app_id": 744059516,
  "doc_id": "<contract-assigned-or-hash-based-id>",
  "explorer_url": "https://testnet.algoexplorer.io/tx/XYZ..."
}
```

### 3) `POST /api/compliproof/verify` (used by verifiers or mock service)

* Request:

```json
{
  "doc_id": "DOC_123",
  "decision": 1,
  "notes": "looks OK"
}
```

* Response: `{ "status": "vote_recorded", "txn_id":"..." }`

### 4) `GET /api/compliproof/status/<doc_id>`

* Returns full status + on-chain metadata + decision history.

---

## IPFS flow

* Frontend uploads file to backend `/upload` → backend pins to IPFS (Pinata/Infura or local ipfs daemon) → returns CID.
* Compute `sha256` locally or backend for double-check.

---

## Verification modes (choose for PoC)

1. **Auto-verify** (fast demo): Backend calls `auto_verify` immediately after `register` to set `compliant`. Good for investor demo.
2. **Mock verifier** (realistic): After register, backend triggers Mock Verifier service which waits N seconds then submits `submit_verification` TX from a verifier account.
3. **Human verifier**: assign a verifier in UI who then clicks Verify.

You can support all three and choose per-upload.

---

## Day-by-day Sprint (7 days)

### Day 1 — Contract spec + TestNet prep (You do contract updates)

* Update PyTeal: add fields (ipfs\_cid, control\_id, framework, owner, attestation\_date, status), logging statements for actions.
* Add `auto_verify` method.
* Deploy to TestNet and note `app_id`.
* Share ABI / method names + expected arg positions to backend dev.

### Day 2 — Backend skeleton & IPFS

* Implement `/upload` endpoint (pin to IPFS).
* Implement `sha256` compute.
* Add config for Algod client + contract `app_id`.
* Implement simple API-key middleware for demo.

### Day 3 — Register flow + on-chain call

* Implement `/register` to:

  * validate payload
  * call contract `register_document` with args
  * return txn\_id and explorer link
* Implement helper to parse contract logs to extract `doc_id`.

### Day 4 — Verification service + mock verifier

* Implement `/verify` endpoint that calls `submit_verification`.
* Implement Mock Verifier worker (background job or small process) which can auto-vote after X seconds or be triggered manually.
* Ensure contract quorum logic is aligned.

### Day 5 — Dashboard + Frontend hooks

* Add UI pages:

  * Upload SBOM + metadata form
  * Submit → shows spinning txn status
  * Dashboard listing docs (fetch `/status/<doc_id>`)
  * Manual Verify button for assigned verifiers
* Integrate Pera Wallet sign for any transactions that need user-signer (owner-initiated actions).

### Day 6 — CompliLedger hook + polling

* Implement simple outbound POST to CompliLedger (or a stub) when `DOC_REGISTERED`/`VERIFICATION_SUBMITTED` events appear.
* Add a 60s polling fallback (indexer/log poll) to capture missed events.
* Run integration tests end-to-end.

### Day 7 — Testing, demo prep, and polish

* Run test cases (see Test checklist below).
* Prepare demo script & sample SBOMs (small) and demo user creds.
* Fix remaining bugs, ensure explorer links work, prepare 5-min investor demo flow.

---

## Minimal infra & env vars

* `ALGOD_TOKEN`, `ALGOD_ADDRESS`, `ALGOD_PORT`
* `APP_ID` (contract id)
* `IPFS_API_KEY`, `IPFS_SECRET` (if using Pinata/Infura)
* `API_KEY_DEMO` for inbound CompliLedger calls
* Verifier/Service account mnemonics (for demo only; store in env)

---

## Security notes (PoC)

* Never store production private keys in repo.
* For PoC, env-based mnemonics OK; for production, use KMS/vault.
* Use API key + origin checks to reduce abuse on demo endpoints.

---

## Demo script (2-3 minutes)

1. Login with Pera (Owner wallet).
2. Upload `sample_sbom.json` → backend returns CID + hash.
3. Fill control ID `AC-2` + framework `OSCAL-NIST-800-53` → Submit.
4. Show explorer txn and `doc_id` visible in dashboard with `status=pending` (or `compliant` if auto-verify).
5. If mock verifier: show worker auto-submitting vote → dashboard updates to `compliant`.
6. Click `View on Explorer` → show immutable record.
7. (Optional) Show CompliLedger receives webhook with proof metadata.

---

## Test checklist

* [ ] Upload returns valid IPFS CID & sha256.
* [ ] Register creates Algorand txn + explorer link.
* [ ] `GET /status/<doc_id>` returns metadata and IPFS link.
* [ ] Auto-verify or mock-verifier correctly transitions status.
* [ ] Assigned verifiers cannot vote twice.
* [ ] Dispute resets status to `under_review` (optional).
* [ ] Demo flow runs under 3 minutes.

---

## Example curl (register)

```bash
# after upload returns ipfs_cid & sha256
curl -X POST https://your-backend/api/compliproof/register \
  -H "x-api-key: DEMOKEY" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_hash":"a1b2c3...",
    "ipfs_cid":"bafy...",
    "control_id":"AC-2",
    "framework":"OSCAL-NIST-800-53",
    "version":"1.0"
  }'
```

Response shows `txn_id`, `doc_id`, `explorer_url`.

---

If you want I can immediately:

* produce the **exact request/arg ordering** your PyTeal `register_document` method must expect (so your contract and backend match), **or**
* scaffold the backend endpoints in Flask/FastAPI (boilerplate) ready to run.

Which of those do you want now?
