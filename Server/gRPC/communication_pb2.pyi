from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Operation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ADD_FILES: _ClassVar[Operation]
    ADD_TAGS: _ClassVar[Operation]
    DELETE: _ClassVar[Operation]
    DELETE_TAGS: _ClassVar[Operation]
    LIST: _ClassVar[Operation]
    FILE_CONTENT: _ClassVar[Operation]
    SEND_RAW_DATABASE_REPLICA: _ClassVar[Operation]
    ADD_REFERENCES: _ClassVar[Operation]
    DELETE_FILES_REPLICAS: _ClassVar[Operation]
    DELETE_FILES_REFERENCES: _ClassVar[Operation]
    ADD_TAGS_TO_REFERED_FILES: _ClassVar[Operation]
    ADD_TAGS_TO_REPLICATED_FILES: _ClassVar[Operation]
    DELETE_TAGS_FROM_REFERED_FILES: _ClassVar[Operation]
    DELETE_TAGS_FROM_REPLICATED_FILES: _ClassVar[Operation]
    NODE_ENTRANCE_REQUEST: _ClassVar[Operation]
    UPDATE_FINGER_TABLE: _ClassVar[Operation]
    UPDATE_FINGER_TABLE_FORWARD: _ClassVar[Operation]
ADD_FILES: Operation
ADD_TAGS: Operation
DELETE: Operation
DELETE_TAGS: Operation
LIST: Operation
FILE_CONTENT: Operation
SEND_RAW_DATABASE_REPLICA: Operation
ADD_REFERENCES: Operation
DELETE_FILES_REPLICAS: Operation
DELETE_FILES_REFERENCES: Operation
ADD_TAGS_TO_REFERED_FILES: Operation
ADD_TAGS_TO_REPLICATED_FILES: Operation
DELETE_TAGS_FROM_REFERED_FILES: Operation
DELETE_TAGS_FROM_REPLICATED_FILES: Operation
NODE_ENTRANCE_REQUEST: Operation
UPDATE_FINGER_TABLE: Operation
UPDATE_FINGER_TABLE_FORWARD: Operation

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

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class FileGeneralInfoss(_message.Message):
    __slots__ = ("files_general_info",)
    FILES_GENERAL_INFO_FIELD_NUMBER: _ClassVar[int]
    files_general_info: _containers.RepeatedCompositeFieldContainer[FileGeneralInfo]
    def __init__(self, files_general_info: _Optional[_Iterable[_Union[FileGeneralInfo, _Mapping]]] = ...) -> None: ...

class ServerID(_message.Message):
    __slots__ = ("serverID",)
    SERVERID_FIELD_NUMBER: _ClassVar[int]
    serverID: int
    def __init__(self, serverID: _Optional[int] = ...) -> None: ...

class ChordNodeReference(_message.Message):
    __slots__ = ("id", "ip", "port")
    ID_FIELD_NUMBER: _ClassVar[int]
    IP_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    id: int
    ip: str
    port: int
    def __init__(self, id: _Optional[int] = ..., ip: _Optional[str] = ..., port: _Optional[int] = ...) -> None: ...

class RingOperationRequest(_message.Message):
    __slots__ = ("requesting_node", "searching_id", "requested_operation", "operation_id")
    REQUESTING_NODE_FIELD_NUMBER: _ClassVar[int]
    SEARCHING_ID_FIELD_NUMBER: _ClassVar[int]
    REQUESTED_OPERATION_FIELD_NUMBER: _ClassVar[int]
    OPERATION_ID_FIELD_NUMBER: _ClassVar[int]
    requesting_node: ChordNodeReference
    searching_id: int
    requested_operation: Operation
    operation_id: int
    def __init__(self, requesting_node: _Optional[_Union[ChordNodeReference, _Mapping]] = ..., searching_id: _Optional[int] = ..., requested_operation: _Optional[_Union[Operation, str]] = ..., operation_id: _Optional[int] = ...) -> None: ...

class OperationDescription(_message.Message):
    __slots__ = ("requested_operation", "node_reference", "id_founded", "operation_id")
    REQUESTED_OPERATION_FIELD_NUMBER: _ClassVar[int]
    NODE_REFERENCE_FIELD_NUMBER: _ClassVar[int]
    ID_FOUNDED_FIELD_NUMBER: _ClassVar[int]
    OPERATION_ID_FIELD_NUMBER: _ClassVar[int]
    requested_operation: Operation
    node_reference: ChordNodeReference
    id_founded: int
    operation_id: int
    def __init__(self, requested_operation: _Optional[_Union[Operation, str]] = ..., node_reference: _Optional[_Union[ChordNodeReference, _Mapping]] = ..., id_founded: _Optional[int] = ..., operation_id: _Optional[int] = ...) -> None: ...

class OperationReceived(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class FilesToAddWithLocation(_message.Message):
    __slots__ = ("files", "tags", "location_hash")
    FILES_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    LOCATION_HASH_FIELD_NUMBER: _ClassVar[int]
    files: _containers.RepeatedCompositeFieldContainer[FileContent]
    tags: _containers.RepeatedScalarFieldContainer[str]
    location_hash: int
    def __init__(self, files: _Optional[_Iterable[_Union[FileContent, _Mapping]]] = ..., tags: _Optional[_Iterable[str]] = ..., location_hash: _Optional[int] = ...) -> None: ...

class FileReference(_message.Message):
    __slots__ = ("title", "file_hash")
    TITLE_FIELD_NUMBER: _ClassVar[int]
    FILE_HASH_FIELD_NUMBER: _ClassVar[int]
    title: str
    file_hash: int
    def __init__(self, title: _Optional[str] = ..., file_hash: _Optional[int] = ...) -> None: ...

class FilesReferencesToAdd(_message.Message):
    __slots__ = ("location_hash", "files_references", "tags")
    LOCATION_HASH_FIELD_NUMBER: _ClassVar[int]
    FILES_REFERENCES_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    location_hash: int
    files_references: _containers.RepeatedCompositeFieldContainer[FileReference]
    tags: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, location_hash: _Optional[int] = ..., files_references: _Optional[_Iterable[_Union[FileReference, _Mapping]]] = ..., tags: _Optional[_Iterable[str]] = ...) -> None: ...

class FilesReferences(_message.Message):
    __slots__ = ("files_references",)
    FILES_REFERENCES_FIELD_NUMBER: _ClassVar[int]
    files_references: _containers.RepeatedCompositeFieldContainer[FileReference]
    def __init__(self, files_references: _Optional[_Iterable[_Union[FileReference, _Mapping]]] = ...) -> None: ...

class UpdateRequestArguments(_message.Message):
    __slots__ = ("files", "tag_list")
    FILES_FIELD_NUMBER: _ClassVar[int]
    TAG_LIST_FIELD_NUMBER: _ClassVar[int]
    files: FilesReferences
    tag_list: TagList
    def __init__(self, files: _Optional[_Union[FilesReferences, _Mapping]] = ..., tag_list: _Optional[_Union[TagList, _Mapping]] = ...) -> None: ...

class UpdateTagsRequest(_message.Message):
    __slots__ = ("args", "operation_tags")
    ARGS_FIELD_NUMBER: _ClassVar[int]
    OPERATION_TAGS_FIELD_NUMBER: _ClassVar[int]
    args: UpdateRequestArguments
    operation_tags: TagList
    def __init__(self, args: _Optional[_Union[UpdateRequestArguments, _Mapping]] = ..., operation_tags: _Optional[_Union[TagList, _Mapping]] = ...) -> None: ...

class FilesToReplicate(_message.Message):
    __slots__ = ("files", "location_hash", "main_replica_node_reference")
    FILES_FIELD_NUMBER: _ClassVar[int]
    LOCATION_HASH_FIELD_NUMBER: _ClassVar[int]
    MAIN_REPLICA_NODE_REFERENCE_FIELD_NUMBER: _ClassVar[int]
    files: FilesToAdd
    location_hash: int
    main_replica_node_reference: ChordNodeReference
    def __init__(self, files: _Optional[_Union[FilesToAdd, _Mapping]] = ..., location_hash: _Optional[int] = ..., main_replica_node_reference: _Optional[_Union[ChordNodeReference, _Mapping]] = ...) -> None: ...

class RawDatabases(_message.Message):
    __slots__ = ("db_phisical", "db_references")
    DB_PHISICAL_FIELD_NUMBER: _ClassVar[int]
    DB_REFERENCES_FIELD_NUMBER: _ClassVar[int]
    db_phisical: bytes
    db_references: bytes
    def __init__(self, db_phisical: _Optional[bytes] = ..., db_references: _Optional[bytes] = ...) -> None: ...

class FilesToUpdateRquest(_message.Message):
    __slots__ = ("args", "node_reference")
    ARGS_FIELD_NUMBER: _ClassVar[int]
    NODE_REFERENCE_FIELD_NUMBER: _ClassVar[int]
    args: UpdateRequestArguments
    node_reference: ChordNodeReference
    def __init__(self, args: _Optional[_Union[UpdateRequestArguments, _Mapping]] = ..., node_reference: _Optional[_Union[ChordNodeReference, _Mapping]] = ...) -> None: ...

class ChordNodeReferences(_message.Message):
    __slots__ = ("references",)
    REFERENCES_FIELD_NUMBER: _ClassVar[int]
    references: _containers.RepeatedCompositeFieldContainer[ChordNodeReference]
    def __init__(self, references: _Optional[_Iterable[_Union[ChordNodeReference, _Mapping]]] = ...) -> None: ...

class LiveAnswer(_message.Message):
    __slots__ = ("any_changes", "next_nodes_list")
    ANY_CHANGES_FIELD_NUMBER: _ClassVar[int]
    NEXT_NODES_LIST_FIELD_NUMBER: _ClassVar[int]
    any_changes: bool
    next_nodes_list: ChordNodeReferences
    def __init__(self, any_changes: bool = ..., next_nodes_list: _Optional[_Union[ChordNodeReferences, _Mapping]] = ...) -> None: ...

class NodeEntranceRequest(_message.Message):
    __slots__ = ("new_node_reference", "claiming_id")
    NEW_NODE_REFERENCE_FIELD_NUMBER: _ClassVar[int]
    CLAIMING_ID_FIELD_NUMBER: _ClassVar[int]
    new_node_reference: ChordNodeReference
    claiming_id: int
    def __init__(self, new_node_reference: _Optional[_Union[ChordNodeReference, _Mapping]] = ..., claiming_id: _Optional[int] = ...) -> None: ...

class IAmYourNextRequest(_message.Message):
    __slots__ = ("next_list", "prev", "assigned_id")
    NEXT_LIST_FIELD_NUMBER: _ClassVar[int]
    PREV_FIELD_NUMBER: _ClassVar[int]
    ASSIGNED_ID_FIELD_NUMBER: _ClassVar[int]
    next_list: ChordNodeReferences
    prev: ChordNodeReference
    assigned_id: int
    def __init__(self, next_list: _Optional[_Union[ChordNodeReferences, _Mapping]] = ..., prev: _Optional[_Union[ChordNodeReference, _Mapping]] = ..., assigned_id: _Optional[int] = ...) -> None: ...

class FileToTransfer(_message.Message):
    __slots__ = ("file", "tags", "location")
    FILE_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    file: FileContent
    tags: _containers.RepeatedScalarFieldContainer[str]
    location: FileLocation
    def __init__(self, file: _Optional[_Union[FileContent, _Mapping]] = ..., tags: _Optional[_Iterable[str]] = ..., location: _Optional[_Union[FileLocation, _Mapping]] = ...) -> None: ...

class FilesAllotmentTransferRequest(_message.Message):
    __slots__ = ("files",)
    FILES_FIELD_NUMBER: _ClassVar[int]
    files: _containers.RepeatedCompositeFieldContainer[FileToTransfer]
    def __init__(self, files: _Optional[_Iterable[_Union[FileToTransfer, _Mapping]]] = ...) -> None: ...

class UpdateReplicationCliqueRequest(_message.Message):
    __slots__ = ("clique", "new_leader", "old_leader")
    CLIQUE_FIELD_NUMBER: _ClassVar[int]
    NEW_LEADER_FIELD_NUMBER: _ClassVar[int]
    OLD_LEADER_FIELD_NUMBER: _ClassVar[int]
    clique: ChordNodeReferences
    new_leader: ChordNodeReference
    old_leader: ChordNodeReference
    def __init__(self, clique: _Optional[_Union[ChordNodeReferences, _Mapping]] = ..., new_leader: _Optional[_Union[ChordNodeReference, _Mapping]] = ..., old_leader: _Optional[_Union[ChordNodeReference, _Mapping]] = ...) -> None: ...

class UpdateFingerTableRequest(_message.Message):
    __slots__ = ("node_reference", "updates_so_far", "remaining_updates", "interval_gap")
    NODE_REFERENCE_FIELD_NUMBER: _ClassVar[int]
    UPDATES_SO_FAR_FIELD_NUMBER: _ClassVar[int]
    REMAINING_UPDATES_FIELD_NUMBER: _ClassVar[int]
    INTERVAL_GAP_FIELD_NUMBER: _ClassVar[int]
    node_reference: ChordNodeReference
    updates_so_far: int
    remaining_updates: int
    interval_gap: int
    def __init__(self, node_reference: _Optional[_Union[ChordNodeReference, _Mapping]] = ..., updates_so_far: _Optional[int] = ..., remaining_updates: _Optional[int] = ..., interval_gap: _Optional[int] = ...) -> None: ...
