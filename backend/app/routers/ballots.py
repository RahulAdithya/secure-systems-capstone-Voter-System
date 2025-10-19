from fastapi import APIRouter, HTTPException, Depends
from app.models import Ballot, VoteRequest, VoteResponse
from app.security import User, require_role

router = APIRouter(prefix="/ballots", tags=["ballots"])

# In-memory ballots (no persistence)
BALLOTS = {
    1: {
        "title": "City Council Election",
        "options": ["Alice Smith", "Bob Jones", "Carol Diaz"],
        "votes": [0, 0, 0],
    },
    2: {
        "title": "Referendum: Approve Park Renovation?",
        "options": ["Yes", "No"],
        "votes": [0, 0],
    },
}

# Track per-user voting to prevent multiple votes per ballot (in-memory).
# Key: (email_lower, ballot_id) -> True
VOTED: dict[tuple[str, int], bool] = {}


@router.get("/tally")
def tally_admin(user: User = Depends(require_role("admin"))):
    out = []
    for bid, data in BALLOTS.items():
        out.append({
            "id": bid,
            "title": data["title"],
            "options": data["options"],
            "votes": data["votes"],
            "totalVotes": sum(data["votes"]),
        })
    return out

@router.get("", response_model=list[Ballot])
def list_ballots():
    out = []
    for bid, data in BALLOTS.items():
        out.append(Ballot(
            id=bid,
            title=data["title"],
            options=data["options"],
            totalVotes=sum(data["votes"])
        ))
    return out

@router.get("/{ballot_id}", response_model=Ballot)
def get_ballot(ballot_id: int):
    b = BALLOTS.get(ballot_id)
    if not b:
        raise HTTPException(status_code=404, detail="Ballot not found")
    return Ballot(
        id=ballot_id,
        title=b["title"],
        options=b["options"],
        totalVotes=sum(b["votes"])
    )

@router.post("/{ballot_id}/vote", response_model=VoteResponse)
def cast_vote(ballot_id: int, payload: VoteRequest, user: User = Depends(require_role("voter"))):
    b = BALLOTS.get(ballot_id)
    if not b:
        raise HTTPException(status_code=404, detail="Ballot not found")
    if payload.option_index < 0 or payload.option_index >= len(b["options"]):
        raise HTTPException(status_code=400, detail="Invalid option index")

    key = ((user.email or "").strip().lower(), ballot_id)
    if VOTED.get(key):
        raise HTTPException(status_code=409, detail="already_voted")
    b["votes"][payload.option_index] += 1
    VOTED[key] = True
    return VoteResponse(
        ballot_id=ballot_id,
        option_index=payload.option_index,
        new_total=sum(b["votes"])
    )


@router.get("/{ballot_id}/status")
def vote_status(ballot_id: int, user: User = Depends(require_role("voter"))):
    key = ((user.email or "").strip().lower(), ballot_id)
    return {"already_voted": bool(VOTED.get(key))}
