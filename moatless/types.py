from typing import List, Optional

from pydantic import BaseModel


class Span(BaseModel):
    start_line: int
    end_line: int
    block_path: List[str] = None
    is_partial: bool = False

    @property
    def span_id(self):
        _span_id = ""
        if self.block_path:
            _span_id += f"{'.'.join(self.block_path)}"

        if self.is_partial:
            _span_id += f"_L{self.start_line}-L{self.end_line}"

        return _span_id

    def __hash__(self):
        return hash((self.start_line, self.end_line)) + hash(str(self.block_path))


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class BaseResponse(BaseModel):
    thoughts: Optional[str] = None
    error: Optional[str] = None
    usage_stats: List[Usage] = []
