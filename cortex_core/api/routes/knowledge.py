"""
Knowledge note CRUD endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from cortex_core.api.models import NoteCreate, NoteResponse, NoteUpdate

router = APIRouter(prefix="/notes", tags=["Knowledge Notes"])


def _engine():
    from cortex_core.api.server import get_engine

    return get_engine()


@router.get("/", response_model=list[NoteResponse])
async def list_notes(
    include_archived: bool = Query(False),
    engine=Depends(_engine),
):
    return engine.list_notes(include_archived=include_archived)


@router.get("/search", response_model=list[NoteResponse])
async def search_notes(q: str = Query(..., min_length=1), engine=Depends(_engine)):
    results = engine.search_notes(q)
    return results


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str, engine=Depends(_engine)):
    note = engine.get_note(note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    return note


@router.post("/", response_model=NoteResponse, status_code=201)
async def create_note(body: NoteCreate, engine=Depends(_engine)):
    return engine.add_note(**body.model_dump())


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: str, body: NoteUpdate, engine=Depends(_engine)):
    fields = body.model_dump(exclude_unset=True)
    note = engine.update_note(note_id, **fields)
    if not note:
        raise HTTPException(404, "Note not found")
    return note


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: str, engine=Depends(_engine)):
    if not engine.delete_note(note_id):
        raise HTTPException(404, "Note not found")
