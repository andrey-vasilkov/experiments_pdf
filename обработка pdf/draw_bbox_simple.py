import json
import sys
from pdf2image import convert_from_path
from PIL import Image, ImageDraw

def draw_bboxes(pdf_path, json_path="coordinates.json", dpi=150):
    with open(json_path, "r", encoding="utf-8") as f:
        elements = json.load(f)

    # Конвертируем PDF в изображения с заданным DPI
    images = convert_from_path(pdf_path, dpi=dpi)
    # Коэффициент перевода пунктов в пиксели: 1 pt = dpi/72 px
    scale = dpi / 72.0

    for page_idx, img in enumerate(images):
        draw = ImageDraw.Draw(img)
        page_elements = [el for el in elements if el.get("page") == page_idx + 1]
        print(f"Страница {page_idx+1}: {len(page_elements)} элементов")

        for el in page_elements:
            x0, y0, x1, y1 = el["bbox"]
            # Упорядочиваем координаты
            if x1 < x0:
                x0, x1 = x1, x0
            if y1 < y0:
                y0, y1 = y1, y0
            # Пропускаем вырожденные
            if x1 <= x0 or y1 <= y0:
                continue
            # Масштабируем
            px0 = int(x0 * scale)
            py0 = int(y0 * scale)
            px1 = int(x1 * scale)
            py1 = int(y1 * scale)
            draw.rectangle([px0, py0, px1, py1], outline="red", width=2)

        img.save(f"page_{page_idx+1}_bbox.png")
        print(f"Сохранено: page_{page_idx+1}_bbox.png")

    print("Готово")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Укажите путь к PDF")
        sys.exit(1)
    draw_bboxes(sys.argv[1])
