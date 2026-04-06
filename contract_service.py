from docxtpl import DocxTemplate
from datetime import datetime
import os


def generate_contract(data: dict) -> str:
    """
    Берёт шаблон templates/contract_template.docx,
    подставляет данные и сохраняет файл в output/.
    Возвращает путь к готовому docx.
    """
    template_path = os.path.join("templates", "contract_template.docx")
    doc = DocxTemplate(template_path)

    # Если дату не ввели — ставим сегодняшнюю
    if not data.get("DATE"):
        data["DATE"] = datetime.now().strftime("%d.%m.%Y")

    doc.render(data)

    safe_fio = (data.get("CLIENT_FIO") or "client").replace(" ", "_")
    out_path = os.path.join("output", f"contract_{safe_fio}.docx")
    doc.save(out_path)

    return out_path


