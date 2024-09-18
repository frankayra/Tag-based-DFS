from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TagList(_message.Message):
    __slots__ = ("tags",)
    TAGS_FIELD_NUMBER: _ClassVar[int]
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, tags: _Optional[_Iterable[str]] = ...) -> None: ...

class TagQuery(_message.Message):
    __slots__ = ("tags_query", "operation_tags")
    TAGS_QUERY_FIELD_NUMBER: _ClassVar[int]
    OPERATION_TAGS_FIELD_NUMBER: _ClassVar[int]
    tags_query: _containers.RepeatedScalarFieldContainer[str]
    operation_tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, tags_query: _Optional[_Iterable[str]] = ..., operation_tags: _Optional[_Iterable[str]] = ...) -> None: ...

class FileContent(_message.Message):
    __slots__ = ("title", "content")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    title: str
    content: str
    def __init__(self, title: _Optional[str] = ..., content: _Optional[str] = ...) -> None: ...

class FilesToAdd(_message.Message):
    __slots__ = ("files", "tags")
    FILES_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    files: _containers.RepeatedCompositeFieldContainer[FileContent]
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, files: _Optional[_Iterable[_Union[FileContent, _Mapping]]] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...

class OperationResult(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class FileLocation(_message.Message):
    __slots__ = ("file_hash", "location_hash")
    FILE_HASH_FIELD_NUMBER: _ClassVar[int]
    LOCATION_HASH_FIELD_NUMBER: _ClassVar[int]
    file_hash: str
    location_hash: int
    def __init__(self, file_hash: _Optional[str] = ..., location_hash: _Optional[int] = ...) -> None: ...

class FileGeneralInfo(_message.Message):
    __slots__ = ("title", "location", "tag_list")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    TAG_LIST_FIELD_NUMBER: _ClassVar[int]
    title: str
    location: FileLocation
    tag_list: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, title: _Optional[str] = ..., location: _Optional[_Union[FileLocation, _Mapping]] = ..., tag_list: _Optional[_Iterable[str]] = ...) -> None: ...
