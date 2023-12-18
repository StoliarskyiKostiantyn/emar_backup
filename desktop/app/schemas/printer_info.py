from pydantic import BaseModel, Field


class PrinterInfo(BaseModel):
    """
    {
        "PrinterStatus":  0,
        "Name":  "Microsoft Print to PDF"
    }
    """

    printer_status: int = Field(1, alias="PrinterStatus")
    name: str = Field("unknown", alias="Name")
