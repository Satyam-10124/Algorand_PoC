from pyteal import *

class VotingContract:
    """
    A simple voting smart contract with multiple candidates
    """
    
    def __init__(self):
        # Global state keys - Changed to match integer storage
        self.candidate_1_votes = Bytes("candidate_1_votes")
        self.candidate_2_votes = Bytes("candidate_2_votes") 
        self.candidate_3_votes = Bytes("candidate_3_votes")
        self.total_votes = Bytes("total_votes")
        self.voting_end = Bytes("voting_end")
        self.creator = Bytes("creator")
        
        # Local state key to track if user has voted
        self.has_voted = Bytes("voted")
    
    def approval_program(self):
        """Main approval program"""
        
        # Application creation
        on_creation = Seq([
            App.globalPut(self.candidate_1_votes, Int(0)),
            App.globalPut(self.candidate_2_votes, Int(0)),
            App.globalPut(self.candidate_3_votes, Int(0)),
            App.globalPut(self.total_votes, Int(0)),
            App.globalPut(self.creator, Txn.sender()),
            # Set voting period (24 hours from creation)
            App.globalPut(self.voting_end, Global.latest_timestamp() + Int(86400)),
            Return(Int(1))
        ])
        
        # Vote for candidate
        vote = Seq([
            # Check if voting period is still active
            Assert(Global.latest_timestamp() < App.globalGet(self.voting_end)),
            
            # Check if user hasn't voted before
            Assert(App.localGet(Txn.sender(), self.has_voted) == Int(0)),
            
            # Get candidate choice from application args
            If(Txn.application_args[1] == Bytes("1"))
            .Then(
                App.globalPut(
                    self.candidate_1_votes,
                    App.globalGet(self.candidate_1_votes) + Int(1)
                )
            )
            .ElseIf(Txn.application_args[1] == Bytes("2"))
            .Then(
                App.globalPut(
                    self.candidate_2_votes,
                    App.globalGet(self.candidate_2_votes) + Int(1)
                )
            )
            .ElseIf(Txn.application_args[1] == Bytes("3"))
            .Then(
                App.globalPut(
                    self.candidate_3_votes,
                    App.globalGet(self.candidate_3_votes) + Int(1)
                )
            )
            .Else(Return(Int(0))),  # Invalid candidate
            
            # Mark user as voted and increment total
            App.localPut(Txn.sender(), self.has_voted, Int(1)),
            App.globalPut(self.total_votes, App.globalGet(self.total_votes) + Int(1)),
            Return(Int(1))
        ])
        
        # Get results (read-only)
        get_results = Return(Int(1))  # Always allow reading state
        
        # Handle different application calls
        program = Cond(
            [Txn.application_id() == Int(0), on_creation],
            [Txn.on_completion() == OnComplete.OptIn, Return(Int(1))],
            [Txn.application_args[0] == Bytes("vote"), vote],
            [Txn.application_args[0] == Bytes("results"), get_results],
        )
        
        return program
    
    def clear_state_program(self):
        """Clear state program - always approve"""
        return Return(Int(1))

# Create contract instance and compile
voting_contract = VotingContract()

def get_approval_program():
    return compileTeal(voting_contract.approval_program(), Mode.Application, version=8)

def get_clear_program():
    return compileTeal(voting_contract.clear_state_program(), Mode.Application, version=8)
