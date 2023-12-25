from pydantic import BaseModel, RootModel


class RouteModel(BaseModel):
    name: str
    route: str
    plane: str
    floor: str
    position: tuple[float, float]


RouteListModel = RootModel[list[RouteModel]]
