from docxtpl import DocxTemplate
from datetime import datetime
import os


def generate_contract(data: dict) -> str:
    template_path = os.path.join("templates", "contract_template.docx")
    doc = DocxTemplate(template_path)

    if not data.get("DATE"):
        data["DATE"] = datetime.now().strftime("%d.%m.%Y")

    doc.render(data)

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    safe_fio = (data.get("CLIENT_FIO") or "client").replace(" ", "_")
    out_path = os.path.join(output_dir, f"contract_{safe_fio}.docx")

    doc.save(out_path)

    return out_path