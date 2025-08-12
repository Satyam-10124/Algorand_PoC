Got it — we’ll add a **simple, professional-grade user authentication model** into the spec so it’s clear how identity and permissions are handled inside the contract, while keeping it blockchain-native (no email/password mess).

Here’s your **updated Markdown doc** with **user-based authentication** included.

---

# **Algorand Compliance DApp – Open Access Smart Contract Specification (with User Authentication)**

## **Overview**

This smart contract enables **anyone** to participate in the compliance proof workflow while maintaining **trust, transparency, and security**.
It expands the original admin–verifier–public model to allow **self-service onboarding** and **decentralized verification**, with **built-in blockchain-based authentication**.

---

## **Authentication Model**

Instead of storing private credentials on-chain, authentication is **wallet-signature-based**:

1. **Identity** = Algorand public address.
2. **Authentication** = User proves control of their address by signing the transaction calling a method.
3. **Authorization** = Smart contract checks the sender’s role before executing actions.

### **User Identity State**

* **Global State (role registry)**: `(address → role_id)`
* **Optional Username/Label**: Stored in local state (non-sensitive, purely for UI display).
* **Registered Flag**: Boolean to indicate if the address has completed onboarding.

---

## **Role Model**

| Role ID | Role Name      | Permissions                                           |
| ------- | -------------- | ----------------------------------------------------- |
| 0       | Public Viewer  | View status, logs                                     |
| 1       | Document Owner | Submit, assign verifiers, transfer ownership          |
| 2       | Verifier       | Verify compliance, view assigned docs                 |
| 3       | Admin          | Approve verifiers, assign verifiers, resolve disputes |

---

## **Authentication Flow**

1. **Registration**

   * Any wallet calls `register_user(role_id, optional_name)`.
   * Contract stores `(address → role_id)` and optional username.
   * If role request is for Public (0) → auto-approved.
     If Verifier (2) or Admin (3) → marked as “Pending Approval.”

2. **Role Approval**

   * Admin calls `approve_user(address, role_id)` to activate elevated roles.

3. **Action Authorization**

   * Every method checks `address → role_id` before execution.

---

## **Smart Contract Methods**

### **1. register\_user(role\_id, optional\_name)**

* Auto-approve public users.
* Store `optional_name` in local state for UI.
* Mark higher-role requests as pending.

### **2. approve\_user(address, role\_id)**

* Admin-only.
* Updates role registry.

### **3. submit\_document(doc\_hash, metadata)**

* Owner-only.
* Metadata includes:

  * Control ID (e.g., NIST SC-28)
  * Framework Name (NIST, ISO, SOC2, etc.)
  * Event Type (audit finding, remediation, SBOM update)
  * Optional Expiration Date

### **4. assign\_verifiers(doc\_id, \[verifier\_addresses])**

* Owner or Admin only.
* Must choose approved verifiers.

### **5. verify\_document(doc\_id, status)**

* Verifier-only.
* Stores individual decision; updates status when quorum reached.

### **6. raise\_dispute(doc\_id)**

* Open to all registered users.
* Changes status to “Under Review.”

### **7. transfer\_ownership(doc\_id, new\_owner)**

* Owner-only.

### **8. view\_status(doc\_id)**

* Public read.

---

## **Event Logging**

All actions emit structured events:

* **Event Type** (`USER_REGISTERED`, `DOC_SUBMITTED`, `VERIFIED`, `DISPUTED`, `TRANSFERRED`)
* **Actor Address**
* **Doc ID (if applicable)**
* **Timestamp**

---

## **Consensus & Dispute Rules**

* Verification decisions require >50% agreement from assigned verifiers.
* Disputed docs reset to “Under Review” until re-verified.

---

## **Security Controls**

* On-chain role enforcement for every action.
* Wallet-based authentication ensures only address owners can act.
* Prevent duplicate document hashes.
* Role approvals only by admins.

---

## **Example Workflow**

1. Alice registers as a Document Owner with wallet `ADDR_A`.
2. Alice submits `HASH123` with ISO 27001 metadata.
3. Alice assigns 3 approved verifiers.
4. Two verifiers approve → status = Compliant.
5. Bob disputes; status changes to Under Review.
6. Admin reassigns verifiers for fresh check.
7. All steps are logged and public.

---
