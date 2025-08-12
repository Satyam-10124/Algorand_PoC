#!/usr/bin/env python3
# document_compliance.py - A simple compliance attestation contract for Algorand

from pyteal import *

def approval_program():
    # Global state (contract-wide)
    document_hash = Bytes("document_hash")         # Hash of the compliance document
    document_version = Bytes("document_version")   # Version number
    attestation_date = Bytes("attestation_date")   # When compliance was attested
    expiration_date = Bytes("expiration_date")     # When compliance expires
    compliance_status = Bytes("status")            # Current compliance status
    admin = Bytes("admin")                         # Administrator address
    
    # Local state (per-account)
    verifier_role = Bytes("verifier_role")         # Whether account is a verifier
    
    # On creation: initialize contract
    on_creation = Seq([
        App.globalPut(admin, Txn.sender()),
        App.globalPut(compliance_status, Bytes("pending")),
        Return(Int(1))
    ])
    
    # Register document: store document hash, version and dates
    register_document = Seq([
        Assert(Txn.sender() == App.globalGet(admin)),
        Assert(Txn.application_args.length() == Int(4)),
        App.globalPut(document_hash, Txn.application_args[1]),
        App.globalPut(document_version, Txn.application_args[2]),
        App.globalPut(attestation_date, Global.latest_timestamp()),
        App.globalPut(expiration_date, Btoi(Txn.application_args[3])),
        App.globalPut(compliance_status, Bytes("compliant")),
        Return(Int(1))
    ])
    
    # Assign verifier role
    assign_verifier = Seq([
        Assert(Txn.sender() == App.globalGet(admin)),
        Assert(Txn.application_args.length() == Int(2)),
        App.localPut(Txn.accounts[1], verifier_role, Int(1)),
        Return(Int(1))
    ])
    
    # Verify compliance status
    verify_compliance = Seq([
        Assert(App.localGet(Txn.sender(), verifier_role) == Int(1)),
        If(Global.latest_timestamp() > App.globalGet(expiration_date),
           App.globalPut(compliance_status, Bytes("expired")),
           Return(Int(1))),
        Return(Int(1))
    ])
    
    # Handle opt-in
    handle_optin = Return(Int(1))
    
    # Program logic
    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.application_args[0] == Bytes("register"), register_document],
        [Txn.application_args[0] == Bytes("assign_verifier"), assign_verifier],
        [Txn.application_args[0] == Bytes("verify"), verify_compliance]
    )
    
    return program

def clear_state_program():
    return Return(Int(1))

# Compile to TEAL
if __name__ == "__main__":
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    with open(os.path.join(current_dir, "compliance_approval.teal"), "w") as f:
        compiled = compileTeal(approval_program(), Mode.Application, version=6)
        f.write(compiled)
    
    with open(os.path.join(current_dir, "compliance_clear.teal"), "w") as f:
        compiled = compileTeal(clear_state_program(), Mode.Application, version=6)
        f.write(compiled)
