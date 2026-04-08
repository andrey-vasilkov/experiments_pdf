import json
import pandas as pd
from pdf2image import convert_from_path
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib as mpl
from collections import defaultdict

def load_coordinates(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_tables_from_coords(elements):
    """Группирует table_cell по страницам и собирает в DataFrame, выравнивая колонки."""
    pages = defaultdict(list)
    for el in elements:
        if el.get('type') == 'table_cell' and el.get('text', '').strip():
            pages[el['page']].append(el)

    tables = {}
    for page, cells in pages.items():
        # Сортируем ячейки по Y (сверху вниз), затем по X
        cells_sorted = sorted(cells, key=lambda c: (c['bbox'][1], c['bbox'][0]))
        rows = []
        current_row = []
        last_y = None
        y_tolerance = 20  # пикселей (подберите под свой DPI)
        for cell in cells_sorted:
            y_center = (cell['bbox'][1] + cell['bbox'][3]) / 2
            if last_y is None or abs(y_center - last_y) <= y_tolerance:
                current_row.append(cell)
            else:
                if current_row:
                    rows.append(current_row)
                current_row = [cell]
            last_y = y_center
        if current_row:
            rows.append(current_row)

        # Превращаем строки в списки текстов, сортируя по X внутри строки
        table_data = []
        for row in rows:
            row_sorted = sorted(row, key=lambda c: c['bbox'][0])
            table_data.append([c['text'] for c in row_sorted])

        if not table_data:
            continue

        # Находим максимальное количество колонок в любой строке
        max_cols = max(len(row) for row in table_data)

        # Выравниваем все строки до max_cols, добавляя пустые строки в конец каждой строки
        aligned_data = []
        for row in table_data:
            if len(row) < max_cols:
                row += [''] * (max_cols - len(row))
            aligned_data.append(row)

        # Первая строка – заголовки
        if len(aligned_data) > 1:
            headers = aligned_data[0]
            data = aligned_data[1:]
            df = pd.DataFrame(data, columns=headers)
        else:
            df = pd.DataFrame(aligned_data)

        tables[page] = df

    return tables

def draw_bbox_on_image(image, elements_for_page, scale=1.0):
    """Рисует красные рамки на изображении для заданных элементов."""
    draw = ImageDraw.Draw(image)
    for el in elements_for_page:
        x0, y0, x1, y1 = el['bbox']
        # Масштабирование, если нужно (координаты уже в пикселях при dpi=150 в draw_bbox_simple.py)
        px0, py0, px1, py1 = int(x0*scale), int(y0*scale), int(x1*scale), int(y1*scale)
        draw.rectangle([px0, py0, px1, py1], outline='red', width=2)
    return image

def compare_pdf_table(pdf_path, json_path, dpi=150, output_prefix='compare'):
    """Создаёт изображения сравнения: PDF с рамками и таблица DataFrame рядом."""
    elements = load_coordinates(json_path)
    tables = build_tables_from_coords(elements)

    # Конвертируем PDF в изображения
    images = convert_from_path(pdf_path, dpi=dpi)

    # Группируем элементы по страницам
    from collections import defaultdict
    page_elements = defaultdict(list)
    for el in elements:
        page_elements[el['page']].append(el)

    for page_num, img in enumerate(images, start=1):
        if page_num not in tables:
            print(f'Страница {page_num}: таблиц не найдено.')
            continue

        df = tables[page_num]
        # Рисуем рамки на изображении
        img_with_bbox = draw_bbox_on_image(img.copy(), page_elements.get(page_num, []), scale=1.0)

        # Создаём фигуру matplotlib: слева изображение, справа таблица
        fig, axes = plt.subplots(1, 2, figsize=(16, 10))
        axes[0].imshow(img_with_bbox)
        axes[0].axis('off')
        axes[0].set_title(f'Страница {page_num} с рамками')

        # Отображаем DataFrame
        axes[1].axis('tight')
        axes[1].axis('off')
        # Используем таблицу matplotlib для красивого вывода
        table_data = [df.columns.tolist()] + df.values.tolist()
        table = axes[1].table(cellText=table_data, loc='center', cellLoc='left')
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        axes[1].set_title('Распознанная таблица (DataFrame)')

        plt.tight_layout()
        plt.savefig(f'{output_prefix}_page_{page_num}.png', dpi=200, bbox_inches='tight')
        plt.close()
        print(f'Сохранено: {output_prefix}_page_{page_num}.png')

    print('Готово!')

if __name__ == '__main__':
    compare_pdf_table(
        pdf_path='pasport_esq_cns__105-300.pdf',
        json_path='coordinates.json',
        dpi=150,
        output_prefix='compare'
    )
