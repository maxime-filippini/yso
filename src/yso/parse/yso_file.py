import dataclasses
import re

RGX_BLOCK_BEGIN = re.compile(r"# BEGIN \[([^\]]+)\]")
RGX_BLOCK_END = re.compile(r"# END")


@dataclasses.dataclass
class Block:
    name: str
    content: str
    line_start: int
    line_end: int


def extract_blocks(text: str):
    lines = text.split("\n")
    extracted_blocks: list[Block] = []

    current_block_name: str | None = None
    current_content = []
    i_line_start: int = -1

    for i_line, line in enumerate(lines):
        match_ = RGX_BLOCK_BEGIN.match(line)
        if match_:
            if current_content:
                raise ValueError

            current_block_name = match_.groups()[0]
            i_line_start = i_line
            continue

        if RGX_BLOCK_END.match(line):
            if not current_block_name:
                raise ValueError

            block = Block(
                name=current_block_name,
                content="\n".join(current_content),
                line_start=i_line_start,
                line_end=i_line,
            )
            extracted_blocks.append(block)

            # Reset the current block info before continuing
            current_block_name = None
            current_content = []
            continue

        if current_block_name is not None:
            current_content.append(line)

    return extracted_blocks
