from typing import Annotated

from fastapi import APIRouter, Response
from pydantic import BaseModel, StringConstraints
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from mixmatch.api.deps import SessionDep
from mixmatch.api.errors import ApiError, responses
from mixmatch.db.models import Collection, CollectionTrack, Track
from mixmatch.text import sort_key

router = APIRouter(tags=["collections"])

CollectionName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
]


class CollectionOut(BaseModel):
    id: int
    name: str
    track_count: int


class CollectionIn(BaseModel):
    name: CollectionName


def _get(session: SessionDep, collection_id: int) -> Collection:
    collection = session.get(Collection, collection_id)
    if collection is None:
        raise ApiError(404, "collection_not_found", f"Colecția {collection_id} nu există")
    return collection


def _out(session: SessionDep, collection: Collection) -> CollectionOut:
    count = session.scalar(
        select(func.count()).where(CollectionTrack.collection_id == collection.id)
    )
    return CollectionOut(id=collection.id, name=collection.name, track_count=count or 0)


def _save_name(session: SessionDep, collection: Collection, name: str) -> None:
    collection.name = name
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ApiError(409, "collection_exists", f"Există deja o colecție „{name}”.") from exc


@router.get("/collections", operation_id="list_collections")
def list_collections(session: SessionDep) -> list[CollectionOut]:
    rows = session.execute(
        select(Collection, func.count(CollectionTrack.track_id))
        .outerjoin(CollectionTrack, CollectionTrack.collection_id == Collection.id)
        .group_by(Collection.id)
    ).all()
    rows.sort(key=lambda row: sort_key(row[0].name))
    return [CollectionOut(id=c.id, name=c.name, track_count=n) for c, n in rows]


@router.post(
    "/collections", status_code=201, operation_id="create_collection", responses=responses(409)
)
def create_collection(body: CollectionIn, session: SessionDep) -> CollectionOut:
    collection = Collection(name=body.name)
    session.add(collection)
    _save_name(session, collection, body.name)
    return _out(session, collection)


@router.patch(
    "/collections/{collection_id}",
    operation_id="rename_collection",
    responses=responses(404, 409),
)
def rename_collection(collection_id: int, body: CollectionIn, session: SessionDep) -> CollectionOut:
    collection = _get(session, collection_id)
    _save_name(session, collection, body.name)
    return _out(session, collection)


@router.delete(
    "/collections/{collection_id}",
    status_code=204,
    operation_id="delete_collection",
    responses=responses(404),
)
def delete_collection(collection_id: int, session: SessionDep) -> Response:
    """Șterge colecția; piesele rămân în bibliotecă."""
    session.delete(_get(session, collection_id))
    session.commit()
    return Response(status_code=204)


@router.put(
    "/collections/{collection_id}/tracks/{track_id}",
    operation_id="add_to_collection",
    responses=responses(404),
)
def add_to_collection(collection_id: int, track_id: int, session: SessionDep) -> CollectionOut:
    collection = _get(session, collection_id)
    if session.get(Track, track_id) is None:
        raise ApiError(404, "track_not_found", f"Piesa {track_id} nu există")
    if session.get(CollectionTrack, (collection_id, track_id)) is None:
        session.add(CollectionTrack(collection_id=collection_id, track_id=track_id))
        session.commit()
    return _out(session, collection)


@router.delete(
    "/collections/{collection_id}/tracks/{track_id}",
    operation_id="remove_from_collection",
    responses=responses(404),
)
def remove_from_collection(collection_id: int, track_id: int, session: SessionDep) -> CollectionOut:
    collection = _get(session, collection_id)
    session.execute(
        delete(CollectionTrack).where(
            CollectionTrack.collection_id == collection_id, CollectionTrack.track_id == track_id
        )
    )
    session.commit()
    return _out(session, collection)
