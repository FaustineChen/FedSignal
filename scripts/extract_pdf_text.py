# input: PDF path
# output: extracted text

from pathlib import Path
from pypdf import PdfReader

# extract text from a single PDF file
# args: path to the PDF file
# return: extracted from all pages
def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    pages = []

    # print(f"Number of Pages: {len(reader.pages)}")

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)

    return "\n".join(pages)


# extract text from one PDF and save it as a txt file
def extract_pdf_to_file(pdf_path: str | Path, output_path: str | Path) -> None:
    pdf_path = Path(pdf_path)
    output_path = Path(output_path)

    text = extract_text_from_pdf(pdf_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")

    print(f"Processed: {pdf_path.name}")
    print(f"Extracted {len(text)} characters")
    print(f"Saved: {output_path}")


# def read_precossed_texts(input_dir: str) -> list[tuple[Path, str]]:
#     input_path = Path(input_dir)
#     txt_files = list(input_path.glob("*.txt"))

#     # (filename, context)
#     documents = []
#     for txt_file in txt_files:
#         text = txt_file.read_text(encoding="utf-8")
#         documents.append((txt_file, text))

#     return documents


# extract all PDF files in input_dir and save txt files to output_dir
def extract_folder(input_dir: str, output_dir: str) -> None:
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    output_path.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_path.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files")

    for pdf_file in pdf_files:
        txt_file = output_path / pdf_file.with_suffix(".txt").name

        extract_pdf_to_file(
            pdf_path=pdf_file,
            output_path=txt_file,
        )
        print("=" * 20)



if __name__ == "__main__":
    extract_folder(
        input_dir="data/raw",
        output_dir="data/processed",
    )
