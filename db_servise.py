from sqlalchemy import select
from bd import SessionLocal
from models import Contract


async def save_contract(data: dict):
    async with SessionLocal() as session:
        contract = Contract(
            client_fio=data.get("CLIENT_FIO", ""),
            phone=data.get("PHONE", ""),
            auto_model=data.get("AUTO_MODEL", ""),
            vin=data.get("VIN", ""),
        )
        session.add(contract)
        await session.commit()
        await session.refresh(contract)
        return contract.id


async def get_last_contracts(limit: int = 5):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Contract).order_by(Contract.id.desc()).limit(limit)
        )
        return result.scalars().all()