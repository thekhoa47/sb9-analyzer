from fastapi import APIRouter, Depends, HTTPException, Query
from app.core import get_local_session, get_async_session
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.client import (
    ClientIn,
    ClientOut,
)
from app.models import (
    Client,
    SavedSearch,
    SavedSearchField,
    ClientNotificationPreference,
)
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from typing import Optional


router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=Page[ClientOut])
def list_clients(
    session: Session = Depends(get_local_session),
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

    return paginate(session, stmt, params)


@router.post("", response_model=ClientOut, status_code=201)
async def onboard_new_client(
    payload: ClientIn, session: AsyncSession = Depends(get_async_session)
):
    try:
        # Start a single transaction
        async with session.begin():
            # 1) create client
            client = Client(
                name=payload.name,
                email=payload.email,
                phone=payload.phone,
                address=payload.address,
                is_active=True,
            )
            session.add(client)
            await session.flush()  # assign client.id

            # 2) create saved searches
            for ss in payload.saved_searches or []:
                saved_search = SavedSearch(**ss.model_dump(exclude={"fields"}))
                saved_search.client = client
                session.add(saved_search)
                # 3) create saved search fields
                for ssf in ss.fields:
                    field = SavedSearchField(**ssf.model_dump())
                    field.saved_search = saved_search  # <— link via parent
                    session.add(field)

            # 4) create client_notification_preferences
            for np in payload.notification_preferences:
                pref = ClientNotificationPreference(**np.model_dump())
                pref.client = client  # <— link via parent
                session.add(pref)

        # 3) Return combined response (commit happened on exiting the context)
        new_client = await session.execute(
            select(Client)
            .where(Client.id == client.id)
            .options(
                selectinload(Client.saved_searches).selectinload(SavedSearch.fields),
                selectinload(Client.notification_preferences),
            )
        )
        client_out = new_client.scalar_one()
        if client_out is None:
            raise HTTPException(status_code=404, detail="Client not found after create")

        return ClientOut.model_validate(client_out, from_attributes=True)

    except HTTPException:
        raise
    except Exception as e:
        # optionally inspect IntegrityError, DataError, etc.
        raise HTTPException(status_code=400, detail=str(e))
