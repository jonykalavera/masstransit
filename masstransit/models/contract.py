from pydantic import BaseModel


class Contract(BaseModel):
    """Contract model"""

    @classmethod
    def messageType(cls):
        return [f"{cls.__module__}.{cls.__name__}"]
