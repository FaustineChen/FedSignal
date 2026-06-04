# input: PDF path
# output: extracted text

from pathlib import Path
from pypdf import PdfReader

def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    pages = []

    print(f"Number of Pages: {len(reader.pages)}")

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)

    return "/n".join(pages)

def extract_folder(input_dir: str, output_dir: str) -> None:
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    output_path.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_path.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files")

    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")

        text = extract_text_from_pdf(pdf_file)
        txt_file = output_path / pdf_file.with_suffix(".txt").name
        txt_file.write_text(text, encoding="utf-8")

        print(f"Saved: {txt_file}")
        print(f"Extracted {len(text)} characters")
        print("=" * 20)



if __name__ == "__main__":
    extract_folder(input_dir = "data/raw", output_dir = "data/processed")

    # pdf_path = "data/raw/fomc_statement_20260429.pdf"
    # output_path = "data/processed/fomc_statement_20260429.txt"
    # text = extract_text_from_pdf(pdf_path)

    # Path("data/processed").mkdir(parents = True, exist_ok = True)
    # Path(output_path).write_text(text, encoding="utf-8")

    # print(f"Extracted {len(text)} characters")
    # print(f"Save to {output_path}")

    # print("======== Preview ========")
    # print(text[:1000])

