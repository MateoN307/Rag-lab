import os
import re
from dataclasses import dataclass

# A word made only of "-", ":" and "|" with at least three dashes in a row.
_SEPARATOR_WORD = re.compile(r"[-:|]*-{3,}[-:|]*")

CHUNK_WORDS = 450  # full length of a chunk, in words
OVERLAP_RATIO = 1 / 9  # share of a chunk repeated at the start of the next


@dataclass
class Chunk:
    text: str
    source: str
    index: int


def chunk_dir(dir_path: str, skip: list[str] = ()) -> list[Chunk]:
    """
    Process every .md file under `dir_path` (including subfolders, except the
    folders in `skip`) and return a flat list of Chunk records.
    """
    chunks = []
    for source in find_md_files(dir_path, skip):
        file_path = os.path.join(dir_path, source)
        chunks.extend(chunk_file(file_path, source))

    return chunks


def find_md_files(dir_path: str, skip: list[str] = ()) -> list[str]:
    """
    Walk `dir_path` and every folder inside it, and return the path of each
    .md file found, relative to `dir_path` (e.g. "plans/trip.md"). Folders
    listed in `skip` (paths relative to `dir_path`) and everything inside
    them are left out.

    This is the single definition of "the notes under a folder".
    """
    if not os.path.isdir(dir_path):
        raise ValueError(f"Not a directory: {dir_path}")

    skipped = {os.path.normpath(folder) for folder in skip}
    sources = []
    for current_dir, subdirs, _ in os.walk(dir_path):
        # Removing a folder from `subdirs` in place stops os.walk going into it.
        here = os.path.relpath(current_dir, dir_path)
        subdirs[:] = [
            d for d in subdirs if os.path.normpath(os.path.join(here, d)) not in skipped
        ]
        for file_path in _md_files_in_folder(current_dir):
            sources.append(os.path.relpath(file_path, dir_path))

    return sources


def chunk_file(
    file_path: str, source: str, chunk_words: int = CHUNK_WORDS
) -> list[Chunk]:
    """
    Clean and split a single markdown file's contents into a list of
    Chunk records of up to `chunk_words` words each, where consecutive
    chunks share round(chunk_words * OVERLAP_RATIO) words.
    """
    if not file_path.endswith(".md"):
        raise ValueError(f"Not a markdown file: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    text = _md_parser(text)

    words = text.split()
    total = len(words)

    overlap = round(chunk_words * OVERLAP_RATIO)
    step = chunk_words - overlap

    chunks = []
    start = 0
    index = 0
    while start < total:
        end = start + chunk_words
        chunk_text = " ".join(words[start:end])
        chunks.append(Chunk(text=chunk_text, source=source, index=index))
        start += step
        index += 1

        # This chunk already reached the last word (or its slice ran past
        # the end and got clipped), so any further chunk would only repeat
        # words from this one's overlap.
        if end >= total:
            break

    return chunks


#### Private helpers ####

def _md_parser(text: str) -> str:
    """
    Take the full text of a file already confirmed to be markdown (.md) and
    clean it up for chunking:
      - `![[image embeds]]` are removed entirely
      - `[[wiki links]]` are replaced with their visible label
        (`[[Note Name|Display]]` -> `Display`, `[[Note Name]]` -> `Note Name`)
      - the YAML frontmatter "header" block (the `---` ... `---` block at the
        very top, if present) is stripped
      - words made only of `-`, `:` and `|` that contain a run of three or
        more dashes (table separator rows like `| ------ | :---: |`, and
        `---` dividers) are removed; table pipes and list bullets are kept
    The remaining text is normalized into a single whitespace-separated
    string (no newlines or extra whitespace).
    """
    text = re.sub(r"!\[\[.*?\]\]", "", text)
    text = re.sub(
        r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]",
        lambda m: m.group(2) if m.group(2) else m.group(1),
        text,
    )

    lines = text.splitlines()

    if lines and lines[0] == "---":
        for i in range(1, len(lines)):
            if lines[i] == "---":
                lines = lines[i + 1:]
                break

    text = "\n".join(lines)
    words = [word for word in text.split() if not _SEPARATOR_WORD.fullmatch(word)]
    return " ".join(words)


def _md_files_in_folder(dir_path: str) -> list[str]:
    """
    Look inside `dir_path` only (not its subfolders) and return a flat
    list of full paths to every .md file directly in it. Anything that
    isn't a .md file — including subdirectories — is skipped.
    """
    md_files = []
    for entry in os.listdir(dir_path):
        full_path = os.path.join(dir_path, entry)
        if os.path.isfile(full_path) and entry.endswith(".md"):
            md_files.append(full_path)
    return md_files


#### Debug tool ####

def _inspect_chunks(chunks):
    print(f"Total chunks: {len(chunks)}")

    view = input(
        "View options:\n"
        "  1 - preview every chunk (first 50 characters)\n"
        "  2 - view a specific chunk in full\n"
        "> "
    )

    if view == "1":
        for chunk in chunks:
            print(f"[{chunk.index}] {chunk.source}: {chunk.text[:50]!r}")
    elif view == "2":
        position = int(input(f"Which chunk? (0-{len(chunks) - 1}): "))
        if 0 <= position < len(chunks):
            print(chunks[position])
        else:
            print(f"Out of range: {position}")
    else:
        print(f"Unrecognized option: {view}")


if __name__ == "__main__":
    dir_path = input("Enter directory path to run chunk_dir on: ")
    chunks = chunk_dir(dir_path)
    _inspect_chunks(chunks)
