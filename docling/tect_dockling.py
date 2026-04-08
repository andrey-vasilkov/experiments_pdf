import sys
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

def test_docling(pdf_path: str):
    print(f"Обработка файла: {pdf_path}")

    # Попытка без OCR (если в PDF есть текстовый слой)
    print("\n1. Пробуем без OCR...")
    converter = DocumentConverter()
    try:
        result = converter.convert(pdf_path)
        doc = result.document
        text = doc.export_to_text()
        if text.strip():
            print("✅ Текст успешно извлечён без OCR.")
            print("Первые 500 символов:\n", text[:500])
        else:
            print("⚠️ Текст не найден, возможно, PDF сканированный.")
            raise ValueError("Empty text")
    except Exception as e:
        print(f"❌ Ошибка или нет текста: {e}")
        print("\n2. Пробуем с OCR (русский язык)...")
        pipeline_opts = PdfPipelineOptions(do_ocr=True, ocr_lang="rus")
        converter = DocumentConverter(pipeline_options=pipeline_opts)
        result = converter.convert(pdf_path)
        doc = result.document
        text = doc.export_to_text()
        if text.strip():
            print("✅ Текст извлечён с помощью OCR.")
            print("Первые 500 символов:\n", text[:500])
        else:
            print("❌ Не удалось извлечь текст даже с OCR.")
            sys.exit(1)

    # Дополнительно: вывести структуру (заголовки, таблицы)
    print("\n3. Структура документа:")
    print(f"  - Количество текстовых элементов: {len(list(doc.texts))}")
    tables = list(doc.tables)
    print(f"  - Количество таблиц: {len(tables)}")
    if tables:
        print("    Первая таблица (Markdown):")
        print(tables[0].export_to_markdown()[:500])

    # Сохраняем Markdown для визуального контроля
    with open("output.md", "w", encoding="utf-8") as f:
        f.write(doc.export_to_markdown())
    print("\n✅ Полный Markdown сохранён в output.md")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Укажите путь к PDF-файлу")
        sys.exit(1)
    test_docling(sys.argv[1])
