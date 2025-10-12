from pydantic import BaseModel

class TeacherOut(BaseModel):
    id: int
    identificador: str
    nombre: str
    programa: str | None = None
    estado: str

    class Config:
        from_attributes = True
