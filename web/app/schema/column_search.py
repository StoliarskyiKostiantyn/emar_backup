from pydantic import BaseModel


class ColumnSearch(BaseModel):
    col_name: str
    current_href: str
