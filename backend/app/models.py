from pydantic import BaseModel
from typing import List, Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str  # placeholder string, no real auth yet

class User(BaseModel):
    id: int
    username: str
    full_name: str

class Ballot(BaseModel):
    id: int
    title: str
    options: List[str]
    totalVotes: int

class VoteRequest(BaseModel):
    option_index: int

class VoteResponse(BaseModel):
    ballot_id: int
    option_index: int
    new_total: int
