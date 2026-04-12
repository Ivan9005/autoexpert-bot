from sqlalchemy import select
from bd import SessionLocal
from models import Contract


async def save_contract(data: dict, file_path: str):
    async with SessionLocal() as session:
        contract = Contract(
            client_fio=data.get("CLIENT_FIO", ""),
            reg_address=data.get("REG_ADDRESS", ""),
            phone=data.get("PHONE", ""),
            passport=data.get("PASSPORT", ""),
            passport_issued_by=data.get("PASSPORT_ISSUED_BY", ""),
            passport_issued_date=data.get("PASSPORT_ISSUED_DATE", ""),
            auto_model=data.get("AUTO_MODEL", ""),
            auto_year=data.get("AUTO_YEAR", ""),
            vin=data.get("VIN", ""),
            gos_number=data.get("GOS_NUMBER", ""),
            sts_number=data.get("STS_NUMBER", ""),
            city=data.get("CITY", ""),
            contract_date=data.get("DATE", ""),
            file_path=file_path,
            status="new",
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


async def get_contract_by_id(contract_id: int):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        return result.scalar_one_or_none()


async def update_contract_status(contract_id: int, new_status: str):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        contract = result.scalar_one_or_none()

        if not contract:
            return None

        contract.status = new_status
        await session.commit()
        await session.refresh(contract)
        return contract


async def get_contracts_by_status(status: str, limit: int = 10):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Contract)
            .where(Contract.status == status)
            .order_by(Contract.id.desc())
            .limit(limit)
        )
        return result.scalars().all()


async def get_contract_file_by_id(contract_id: int):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        contract = result.scalar_one_or_none()

        if contract is None:
            return None

        return contract.file_path