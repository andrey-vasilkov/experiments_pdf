import json
import sys
from docling.document_converter import DocumentConverter
from pdf2image import convert_from_path
from PIL import Image, ImageDraw

def normalize_bbox(bbox):
    """Приводит координаты к виду (x0, y0, x1, y1) с x0<=x1 и y0<=y1."""
    x0, y0, x1, y1 = bbox
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))

def extract_coordinates(pdf_path: str, output_json: str = "coordinates.json", visualize: bool = True):
    print(f"Обработка: {pdf_path}")

    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    doc = result.document

    elements = []

    # Текстовые блоки
    for item in doc.texts:
        for prov in item.prov:
            bbox = (prov.bbox.l, prov.bbox.t, prov.bbox.r, prov.bbox.b)
            bbox = normalize_bbox(bbox)
            elements.append({
                "type": item.label,
                "text": item.text,
                "page": prov.page_no,
                "bbox": bbox
            })

    # Ячейки таблиц
    for table in doc.tables:
        for cell in table.data.table_cells:
            if cell.text and cell.text.strip():
                for prov in table.prov:
                    bbox = (cell.bbox.l, cell.bbox.t, cell.bbox.r, cell.bbox.b)
                    bbox = normalize_bbox(bbox)
                    elements.append({
                        "type": "table_cell",
                        "text": cell.text,
                        "page": prov.page_no,
                        "bbox": bbox
                    })

    print(f"Найдено элементов: {len(elements)}")

    # Сохраняем JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(elements, f, ensure_ascii=False, indent=2)
    print(f"Координаты сохранены в {output_json}")

    # Визуализация
    if visualize:
        print("Генерация изображений с рамками...")
        images = convert_from_path(pdf_path, dpi=150)
        for page_idx, img in enumerate(images):
            draw = ImageDraw.Draw(img)
            w, h = img.size
            page_elements = [el for el in elements if el["page"] == page_idx + 1]
            for el in page_elements:
                x0, y0, x1, y1 = el["bbox"]
                # Масштабируем нормализованные координаты (0..1) в пиксели
                px0 = int(x0 * w)
                py0 = int(y0 * h)
                px1 = int(x1 * w)
                py1 = int(y1 * h)
                # Убеждаемся, что координаты в пределах изображения
                px0 = max(0, min(px0, w-1))
                py0 = max(0, min(py0, h-1))
                px1 = max(0, min(px1, w-1))
                py1 = max(0, min(py1, h-1))
                if px1 > px0 and py1 > py0:
                    draw.rectangle([px0, py0, px1, py1], outline="red", width=2)
            img.save(f"page_{page_idx+1}_bbox.png")
            print(f"  Страница {page_idx+1} сохранена как page_{page_idx+1}_bbox.png")

    return elements

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Укажите путь к PDF файлу")
        sys.exit(1)
    extract_coordinates(sys.argv[1])
