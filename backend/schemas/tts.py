from pydantic import Field
from pydantic import BaseModel


class TtsSynthesizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=3000, description="待合成文本")
    voice: str | None = Field(default=None, max_length=64, description="发音人 vcn，默认 x4_xiaoyan")
