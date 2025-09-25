from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.core import get_db
from sqlalchemy.orm import Session
from app.schemas import (
    OnboardNewClientIn,
    OnboardNewClientOut,
    ClientOut,
    SavedSearchOut,
    ClientsWithSearchesOut,
)
from app.models import Client, SavedSearch
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from typing import Optional


router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=OnboardNewClientOut, status_code=201)
def onboard_new_client(payload: OnboardNewClientIn, db: Session = Depends(get_db)):
    try:
        # Start a single transaction
        with db.begin():
            # 1) create client
            client = Client(
                name=payload.name,
                email=payload.email,
                phone=payload.phone,
                # address=payload.address,
            )
            db.add(client)
            db.flush()  # assign client.id

            # 2) create saved searches
            saved_searches = []
            for item in payload.listing_preferences:
                s = SavedSearch(
                    client_id=client.id,
                    name=item.name,
                    city=item.city,
                    beds_min=item.beds_min,
                    baths_min=item.baths_min,
                    max_price=item.max_price,
                    # criteria_json=item.criteria_json,
                )
                db.add(s)
                db.flush()  # get s.id, s.cursor_iso
                # Build output (you can also use Pydantic model_validate if on Pydantic v2)
                saved_searches.append(
                    SavedSearchOut(
                        id=str(s.id),
                        client_id=str(s.client_id),
                        name=s.name,
                        beds_min=s.beds_min,
                        baths_min=s.baths_min,
                        max_price=s.max_price,
                        created_at=s.created_at.isoformat(),
                        updated_at=s.updated_at.isoformat() if s.updated_at else None,
                    )
                )

        # 3) Return combined response (commit happened on exiting the context)
        client_out = ClientOut(
            id=str(client.id),
            name=client.name,
            email=client.email,
            phone=client.phone,
            # address=client.address,
            created_at=client.created_at.isoformat(),
            updated_at=client.updated_at.isoformat() if client.updated_at else None,
        )

        return OnboardNewClientOut(client=client_out, saved_searches=saved_searches)

    except Exception as e:
        # Optionally map DB errors to 4xx
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=Page[ClientsWithSearchesOut])
def list_clients(
    request: Request,
    db: Session = Depends(get_db),
    params: Params = Depends(),  # ?page=1&size=50
    search: Optional[str] = Query(
        None
    ),  # free text over name/email/phone/messenger_psid
):
    # Base selectable (1:1 join + eager load)
    stmt = (
        select(Client)
        .join(Client.saved_searches)
        .options(selectinload(Client.saved_searches))
    )

    # # Filters
    # filters = parse_filters(request.query_params)
    # colmap = {
    #     "sms_opt_in": Client.sms_opt_in,
    #     "email_opt_in": Client.email_opt_in,
    #     "messenger_opt_in": Client.messenger_opt_in,
    # }
    # for field, value in filters:
    #     col = colmap[field]
    #     stmt = stmt.where(col == value)

    # Search over address/city/state (+ “California” -> CA)
    if search:
        needle = search.strip()
        like = f"%{needle}%"
        ors = [
            Client.name.ilike(like),
            Client.email.ilike(like),
            Client.phone.ilike(like),
        ]
        stmt = stmt.where(or_(*ors))

    return paginate(db, stmt, params)


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    c = db.get(Client, client_id)
    if not c:
        raise HTTPException(404)
    return ClientOut(
        id=c.id,
        name=c.name,
        email=c.email,
        phone=c.phone,
        # address=c.address,
    )
