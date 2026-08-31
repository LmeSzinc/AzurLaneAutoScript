"""Pydantic v2 models shared by the webui API routers."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class ApiRequest(BaseModel):
    """Base class for request bodies: reject unknown fields."""

    model_config = ConfigDict(extra="forbid")


class SetValueRequest(ApiRequest):
    value: dict[str, Any]


class RunRequest(ApiRequest):
    instance: str
    func: str | None = None


class StopRequest(ApiRequest):
    instance: str


class LanguageRequest(ApiRequest):
    language: str


class ThemeRequest(ApiRequest):
    theme: str


class NewInstanceRequest(ApiRequest):
    name: str
    origin: str | None = None


class DeleteInstanceRequest(ApiRequest):
    name: str


class RenameInstanceRequest(ApiRequest):
    name: str
    new_name: str


class ImportConfigRequest(ApiRequest):
    config: dict[str, Any]


class InstanceStatus(BaseModel):
    name: str
    state: int
    alive: bool


class StatusResponse(BaseModel):
    instances: list[InstanceStatus]
    theme: str
    language: str


class SchemaResponse(BaseModel):
    menu: dict[str, Any]
    args: dict[str, Any]


class SaveConfigResponse(BaseModel):
    valid: list[str]
    invalid: list[str]


class OkResponse(BaseModel):
    ok: bool
    error: str | None = None


class ThemeResponse(BaseModel):
    theme: str


class LanguageResponse(BaseModel):
    language: str


class UpdateInstallRequest(BaseModel):
    version: str


class RemoteStatusResponse(BaseModel):
    alive: bool
    state: int
    entry_point: str | None = None


class TaskItem(BaseModel):
    command: str
    next_run: str


class SchedulerResponse(BaseModel):
    alive: bool
    running: list[TaskItem]
    pending: list[TaskItem]
    waiting: list[TaskItem]


class ConfigListItem(BaseModel):
    name: str
    modified: str
