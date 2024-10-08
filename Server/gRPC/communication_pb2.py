# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: communication.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'communication.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13\x63ommunication.proto\x12\x12TagBasedFileSystem\"\x17\n\x07TagList\x12\x0c\n\x04tags\x18\x01 \x03(\t\"6\n\x08TagQuery\x12\x12\n\ntags_query\x18\x01 \x03(\t\x12\x16\n\x0eoperation_tags\x18\x02 \x03(\t\"-\n\x0b\x46ileContent\x12\r\n\x05title\x18\x01 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x02 \x01(\t\"J\n\nFilesToAdd\x12.\n\x05\x66iles\x18\x01 \x03(\x0b\x32\x1f.TagBasedFileSystem.FileContent\x12\x0c\n\x04tags\x18\x02 \x03(\t\"3\n\x0fOperationResult\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"8\n\x0c\x46ileLocation\x12\x11\n\tfile_hash\x18\x01 \x01(\t\x12\x15\n\rlocation_hash\x18\x02 \x01(\x05\"f\n\x0f\x46ileGeneralInfo\x12\r\n\x05title\x18\x01 \x01(\t\x12\x32\n\x08location\x18\x02 \x01(\x0b\x32 .TagBasedFileSystem.FileLocation\x12\x10\n\x08tag_list\x18\x03 \x03(\t\"\x07\n\x05\x45mpty\"T\n\x11\x46ileGeneralInfoss\x12?\n\x12\x66iles_general_info\x18\x01 \x03(\x0b\x32#.TagBasedFileSystem.FileGeneralInfo\"\x1c\n\x08ServerID\x12\x10\n\x08serverID\x18\x01 \x01(\x05\":\n\x12\x43hordNodeReference\x12\n\n\x02id\x18\x01 \x01(\x05\x12\n\n\x02ip\x18\x02 \x01(\t\x12\x0c\n\x04port\x18\x03 \x01(\x05\"\xbf\x01\n\x14RingOperationRequest\x12?\n\x0frequesting_node\x18\x01 \x01(\x0b\x32&.TagBasedFileSystem.ChordNodeReference\x12\x14\n\x0csearching_id\x18\x02 \x01(\x05\x12:\n\x13requested_operation\x18\x03 \x01(\x0e\x32\x1d.TagBasedFileSystem.Operation\x12\x14\n\x0coperation_id\x18\x04 \x01(\x05\"\xbc\x01\n\x14OperationDescription\x12:\n\x13requested_operation\x18\x01 \x01(\x0e\x32\x1d.TagBasedFileSystem.Operation\x12>\n\x0enode_reference\x18\x02 \x01(\x0b\x32&.TagBasedFileSystem.ChordNodeReference\x12\x12\n\nid_founded\x18\x03 \x01(\x05\x12\x14\n\x0coperation_id\x18\x04 \x01(\x05\"5\n\x11OperationReceived\x12\x14\n\x07success\x18\x01 \x01(\x08H\x00\x88\x01\x01\x42\n\n\x08_success\"m\n\x16\x46ilesToAddWithLocation\x12.\n\x05\x66iles\x18\x01 \x03(\x0b\x32\x1f.TagBasedFileSystem.FileContent\x12\x0c\n\x04tags\x18\x02 \x03(\t\x12\x15\n\rlocation_hash\x18\x03 \x01(\x05\"1\n\rFileReference\x12\r\n\x05title\x18\x01 \x01(\t\x12\x11\n\tfile_hash\x18\x02 \x01(\x03\"x\n\x14\x46ilesReferencesToAdd\x12\x15\n\rlocation_hash\x18\x01 \x01(\x05\x12;\n\x10\x66iles_references\x18\x02 \x03(\x0b\x32!.TagBasedFileSystem.FileReference\x12\x0c\n\x04tags\x18\x03 \x03(\t\"N\n\x0f\x46ilesReferences\x12;\n\x10\x66iles_references\x18\x01 \x03(\x0b\x32!.TagBasedFileSystem.FileReference\"\x9c\x01\n\x16UpdateRequestArguments\x12\x37\n\x05\x66iles\x18\x01 \x01(\x0b\x32#.TagBasedFileSystem.FilesReferencesH\x00\x88\x01\x01\x12\x32\n\x08tag_list\x18\x02 \x01(\x0b\x32\x1b.TagBasedFileSystem.TagListH\x01\x88\x01\x01\x42\x08\n\x06_filesB\x0b\n\t_tag_list\"\xbd\x01\n\x11UpdateTagsRequest\x12\x38\n\x04\x61rgs\x18\x01 \x01(\x0b\x32*.TagBasedFileSystem.UpdateRequestArguments\x12\x16\n\x0eoperation_tags\x18\x02 \x03(\t\x12\x43\n\x0enode_reference\x18\x03 \x01(\x0b\x32&.TagBasedFileSystem.ChordNodeReferenceH\x00\x88\x01\x01\x42\x11\n\x0f_node_reference\"\xa5\x01\n\x10\x46ilesToReplicate\x12-\n\x05\x66iles\x18\x01 \x01(\x0b\x32\x1e.TagBasedFileSystem.FilesToAdd\x12\x15\n\rlocation_hash\x18\x02 \x01(\x05\x12K\n\x1bmain_replica_node_reference\x18\x03 \x01(\x0b\x32&.TagBasedFileSystem.ChordNodeReference\":\n\x0cRawDatabases\x12\x13\n\x0b\x64\x62_phisical\x18\x01 \x01(\x0c\x12\x15\n\rdb_references\x18\x02 \x01(\x0c\"\x90\x01\n\x14\x46ilesToUpdateRequest\x12\x38\n\x04\x61rgs\x18\x01 \x01(\x0b\x32*.TagBasedFileSystem.UpdateRequestArguments\x12>\n\x0enode_reference\x18\x02 \x01(\x0b\x32&.TagBasedFileSystem.ChordNodeReference\"Q\n\x13\x43hordNodeReferences\x12:\n\nreferences\x18\x01 \x03(\x0b\x32&.TagBasedFileSystem.ChordNodeReference\"|\n\nLiveAnswer\x12\x13\n\x0b\x61ny_changes\x18\x01 \x01(\x08\x12\x45\n\x0fnext_nodes_list\x18\x02 \x01(\x0b\x32\'.TagBasedFileSystem.ChordNodeReferencesH\x00\x88\x01\x01\x42\x12\n\x10_next_nodes_list\"n\n\x13NodeEntranceRequest\x12\x42\n\x12new_node_reference\x18\x01 \x01(\x0b\x32&.TagBasedFileSystem.ChordNodeReference\x12\x13\n\x0b\x63laiming_id\x18\x02 \x01(\x05\"\xb0\x01\n\x12IAmYourNextRequest\x12:\n\tnext_list\x18\x01 \x01(\x0b\x32\'.TagBasedFileSystem.ChordNodeReferences\x12\x34\n\x04prev\x18\x02 \x01(\x0b\x32&.TagBasedFileSystem.ChordNodeReference\x12\x18\n\x0b\x61ssigned_id\x18\x03 \x01(\x05H\x00\x88\x01\x01\x42\x0e\n\x0c_assigned_id\"\x81\x01\n\x0e\x46ileToTransfer\x12-\n\x04\x66ile\x18\x01 \x01(\x0b\x32\x1f.TagBasedFileSystem.FileContent\x12\x0c\n\x04tags\x18\x02 \x03(\t\x12\x32\n\x08location\x18\x03 \x01(\x0b\x32 .TagBasedFileSystem.FileLocation\"R\n\x1d\x46ilesAllotmentTransferRequest\x12\x31\n\x05\x66iles\x18\x01 \x03(\x0b\x32\".TagBasedFileSystem.FileToTransfer\"\xd1\x01\n\x1eUpdateReplicationCliqueRequest\x12\x37\n\x06\x63lique\x18\x01 \x01(\x0b\x32\'.TagBasedFileSystem.ChordNodeReferences\x12:\n\nnew_leader\x18\x02 \x01(\x0b\x32&.TagBasedFileSystem.ChordNodeReference\x12:\n\nold_leader\x18\x03 \x01(\x0b\x32&.TagBasedFileSystem.ChordNodeReference\"\xec\x01\n\x18UpdateFingerTableRequest\x12>\n\x0enode_reference\x18\x01 \x01(\x0b\x32&.TagBasedFileSystem.ChordNodeReference\x12\x1b\n\x0eupdates_so_far\x18\x02 \x01(\x05H\x00\x88\x01\x01\x12\x1e\n\x11remaining_updates\x18\x03 \x01(\x05H\x01\x88\x01\x01\x12\x19\n\x0cinterval_gap\x18\x04 \x01(\x05H\x02\x88\x01\x01\x42\x11\n\x0f_updates_so_farB\x14\n\x12_remaining_updatesB\x0f\n\r_interval_gap*\xad\x03\n\tOperation\x12\r\n\tADD_FILES\x10\x00\x12\x0c\n\x08\x41\x44\x44_TAGS\x10\x01\x12\n\n\x06\x44\x45LETE\x10\x02\x12\x0f\n\x0b\x44\x45LETE_TAGS\x10\x03\x12\x08\n\x04LIST\x10\x04\x12\x10\n\x0c\x46ILE_CONTENT\x10\x05\x12\x1d\n\x19SEND_RAW_DATABASE_REPLICA\x10\x06\x12\x12\n\x0e\x41\x44\x44_REFERENCES\x10\x07\x12\x19\n\x15\x44\x45LETE_FILES_REPLICAS\x10\x08\x12\x1b\n\x17\x44\x45LETE_FILES_REFERENCES\x10\t\x12\x1d\n\x19\x41\x44\x44_TAGS_TO_REFERED_FILES\x10\n\x12 \n\x1c\x41\x44\x44_TAGS_TO_REPLICATED_FILES\x10\x0b\x12\"\n\x1e\x44\x45LETE_TAGS_FROM_REFERED_FILES\x10\x0c\x12%\n!DELETE_TAGS_FROM_REPLICATED_FILES\x10\r\x12\x19\n\x15NODE_ENTRANCE_REQUEST\x10\x0e\x12\x17\n\x13UPDATE_FINGER_TABLE\x10\x0f\x12\x1f\n\x1bUPDATE_FINGER_TABLE_FORWARD\x10\x10\x32\xe5\x03\n\tClientAPI\x12J\n\x04list\x12\x1b.TagBasedFileSystem.TagList\x1a#.TagBasedFileSystem.FileGeneralInfo0\x01\x12P\n\x0b\x66ileContent\x12 .TagBasedFileSystem.FileLocation\x1a\x1f.TagBasedFileSystem.FileContent\x12O\n\x08\x61\x64\x64\x46iles\x12\x1e.TagBasedFileSystem.FilesToAdd\x1a#.TagBasedFileSystem.OperationResult\x12L\n\x07\x61\x64\x64Tags\x12\x1c.TagBasedFileSystem.TagQuery\x1a#.TagBasedFileSystem.OperationResult\x12J\n\x06\x64\x65lete\x12\x1b.TagBasedFileSystem.TagList\x1a#.TagBasedFileSystem.OperationResult\x12O\n\ndeleteTags\x12\x1c.TagBasedFileSystem.TagQuery\x1a#.TagBasedFileSystem.OperationResult2\x97\x16\n\x19\x43hordNetworkCommunication\x12[\n\x08succesor\x12(.TagBasedFileSystem.RingOperationRequest\x1a%.TagBasedFileSystem.OperationReceived\x12i\n\x16proceed_with_operation\x12(.TagBasedFileSystem.OperationDescription\x1a%.TagBasedFileSystem.OperationReceived\x12J\n\x04list\x12\x1b.TagBasedFileSystem.TagList\x1a%.TagBasedFileSystem.FileGeneralInfoss\x12Q\n\x0c\x66ile_content\x12 .TagBasedFileSystem.FileLocation\x1a\x1f.TagBasedFileSystem.FileContent\x12\\\n\tadd_files\x12*.TagBasedFileSystem.FilesToAddWithLocation\x1a#.TagBasedFileSystem.OperationResult\x12M\n\x08\x61\x64\x64_tags\x12\x1c.TagBasedFileSystem.TagQuery\x1a#.TagBasedFileSystem.OperationResult\x12J\n\x06\x64\x65lete\x12\x1b.TagBasedFileSystem.TagList\x1a#.TagBasedFileSystem.OperationResult\x12P\n\x0b\x64\x65lete_tags\x12\x1c.TagBasedFileSystem.TagQuery\x1a#.TagBasedFileSystem.OperationResult\x12V\n\treplicate\x12$.TagBasedFileSystem.FilesToReplicate\x1a#.TagBasedFileSystem.OperationResult\x12\x62\n\x19send_raw_database_replica\x12 .TagBasedFileSystem.RawDatabases\x1a#.TagBasedFileSystem.OperationResult\x12_\n\x0e\x61\x64\x64_references\x12(.TagBasedFileSystem.FilesReferencesToAdd\x1a#.TagBasedFileSystem.OperationResult\x12\x66\n\x15\x64\x65lete_files_replicas\x12(.TagBasedFileSystem.FilesToUpdateRequest\x1a#.TagBasedFileSystem.OperationResult\x12j\n\x17\x64\x65lete_files_references\x12*.TagBasedFileSystem.UpdateRequestArguments\x1a#.TagBasedFileSystem.OperationResult\x12g\n\x19\x61\x64\x64_tags_to_refered_files\x12%.TagBasedFileSystem.UpdateTagsRequest\x1a#.TagBasedFileSystem.OperationResult\x12j\n\x1c\x61\x64\x64_tags_to_replicated_files\x12%.TagBasedFileSystem.UpdateTagsRequest\x1a#.TagBasedFileSystem.OperationResult\x12l\n\x1e\x64\x65lete_tags_from_refered_files\x12%.TagBasedFileSystem.UpdateTagsRequest\x1a#.TagBasedFileSystem.OperationResult\x12o\n!delete_tags_from_replicated_files\x12%.TagBasedFileSystem.UpdateTagsRequest\x1a#.TagBasedFileSystem.OperationResult\x12N\n\theartbeat\x12&.TagBasedFileSystem.ChordNodeReference\x1a\x19.TagBasedFileSystem.Empty\x12J\n\ralive_request\x12\x19.TagBasedFileSystem.Empty\x1a\x1e.TagBasedFileSystem.LiveAnswer\x12Z\n\x0bunreplicate\x12&.TagBasedFileSystem.ChordNodeReference\x1a#.TagBasedFileSystem.OperationResult\x12\x65\n\x15node_entrance_request\x12\'.TagBasedFileSystem.NodeEntranceRequest\x1a#.TagBasedFileSystem.OperationResult\x12_\n\x0ei_am_your_next\x12&.TagBasedFileSystem.IAmYourNextRequest\x1a%.TagBasedFileSystem.OperationReceived\x12\\\n\x0bupdate_next\x12&.TagBasedFileSystem.ChordNodeReference\x1a%.TagBasedFileSystem.OperationReceived\x12r\n\x18\x66iles_allotment_transfer\x12\x31.TagBasedFileSystem.FilesAllotmentTransferRequest\x1a#.TagBasedFileSystem.OperationResult\x12t\n\x19update_replication_clique\x12\x32.TagBasedFileSystem.UpdateReplicationCliqueRequest\x1a#.TagBasedFileSystem.OperationResult\x12]\n\x0ei_am_your_prev\x12&.TagBasedFileSystem.ChordNodeReference\x1a#.TagBasedFileSystem.OperationResult\x12j\n\x13update_finger_table\x12,.TagBasedFileSystem.UpdateFingerTableRequest\x1a%.TagBasedFileSystem.OperationReceived\x12r\n\x1bupdate_finger_table_forward\x12,.TagBasedFileSystem.UpdateFingerTableRequest\x1a%.TagBasedFileSystem.OperationReceived\x12\\\n\x16send_me_your_next_list\x12\x19.TagBasedFileSystem.Empty\x1a\'.TagBasedFileSystem.ChordNodeReferencesB6\n\x1bio.grpc.examples.helloworldB\x0fHelloWorldProtoP\x01\xa2\x02\x03HLWb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'communication_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'\n\033io.grpc.examples.helloworldB\017HelloWorldProtoP\001\242\002\003HLW'
  _globals['_OPERATION']._serialized_start=3345
  _globals['_OPERATION']._serialized_end=3774
  _globals['_TAGLIST']._serialized_start=43
  _globals['_TAGLIST']._serialized_end=66
  _globals['_TAGQUERY']._serialized_start=68
  _globals['_TAGQUERY']._serialized_end=122
  _globals['_FILECONTENT']._serialized_start=124
  _globals['_FILECONTENT']._serialized_end=169
  _globals['_FILESTOADD']._serialized_start=171
  _globals['_FILESTOADD']._serialized_end=245
  _globals['_OPERATIONRESULT']._serialized_start=247
  _globals['_OPERATIONRESULT']._serialized_end=298
  _globals['_FILELOCATION']._serialized_start=300
  _globals['_FILELOCATION']._serialized_end=356
  _globals['_FILEGENERALINFO']._serialized_start=358
  _globals['_FILEGENERALINFO']._serialized_end=460
  _globals['_EMPTY']._serialized_start=462
  _globals['_EMPTY']._serialized_end=469
  _globals['_FILEGENERALINFOSS']._serialized_start=471
  _globals['_FILEGENERALINFOSS']._serialized_end=555
  _globals['_SERVERID']._serialized_start=557
  _globals['_SERVERID']._serialized_end=585
  _globals['_CHORDNODEREFERENCE']._serialized_start=587
  _globals['_CHORDNODEREFERENCE']._serialized_end=645
  _globals['_RINGOPERATIONREQUEST']._serialized_start=648
  _globals['_RINGOPERATIONREQUEST']._serialized_end=839
  _globals['_OPERATIONDESCRIPTION']._serialized_start=842
  _globals['_OPERATIONDESCRIPTION']._serialized_end=1030
  _globals['_OPERATIONRECEIVED']._serialized_start=1032
  _globals['_OPERATIONRECEIVED']._serialized_end=1085
  _globals['_FILESTOADDWITHLOCATION']._serialized_start=1087
  _globals['_FILESTOADDWITHLOCATION']._serialized_end=1196
  _globals['_FILEREFERENCE']._serialized_start=1198
  _globals['_FILEREFERENCE']._serialized_end=1247
  _globals['_FILESREFERENCESTOADD']._serialized_start=1249
  _globals['_FILESREFERENCESTOADD']._serialized_end=1369
  _globals['_FILESREFERENCES']._serialized_start=1371
  _globals['_FILESREFERENCES']._serialized_end=1449
  _globals['_UPDATEREQUESTARGUMENTS']._serialized_start=1452
  _globals['_UPDATEREQUESTARGUMENTS']._serialized_end=1608
  _globals['_UPDATETAGSREQUEST']._serialized_start=1611
  _globals['_UPDATETAGSREQUEST']._serialized_end=1800
  _globals['_FILESTOREPLICATE']._serialized_start=1803
  _globals['_FILESTOREPLICATE']._serialized_end=1968
  _globals['_RAWDATABASES']._serialized_start=1970
  _globals['_RAWDATABASES']._serialized_end=2028
  _globals['_FILESTOUPDATEREQUEST']._serialized_start=2031
  _globals['_FILESTOUPDATEREQUEST']._serialized_end=2175
  _globals['_CHORDNODEREFERENCES']._serialized_start=2177
  _globals['_CHORDNODEREFERENCES']._serialized_end=2258
  _globals['_LIVEANSWER']._serialized_start=2260
  _globals['_LIVEANSWER']._serialized_end=2384
  _globals['_NODEENTRANCEREQUEST']._serialized_start=2386
  _globals['_NODEENTRANCEREQUEST']._serialized_end=2496
  _globals['_IAMYOURNEXTREQUEST']._serialized_start=2499
  _globals['_IAMYOURNEXTREQUEST']._serialized_end=2675
  _globals['_FILETOTRANSFER']._serialized_start=2678
  _globals['_FILETOTRANSFER']._serialized_end=2807
  _globals['_FILESALLOTMENTTRANSFERREQUEST']._serialized_start=2809
  _globals['_FILESALLOTMENTTRANSFERREQUEST']._serialized_end=2891
  _globals['_UPDATEREPLICATIONCLIQUEREQUEST']._serialized_start=2894
  _globals['_UPDATEREPLICATIONCLIQUEREQUEST']._serialized_end=3103
  _globals['_UPDATEFINGERTABLEREQUEST']._serialized_start=3106
  _globals['_UPDATEFINGERTABLEREQUEST']._serialized_end=3342
  _globals['_CLIENTAPI']._serialized_start=3777
  _globals['_CLIENTAPI']._serialized_end=4262
  _globals['_CHORDNETWORKCOMMUNICATION']._serialized_start=4265
  _globals['_CHORDNETWORKCOMMUNICATION']._serialized_end=7104
# @@protoc_insertion_point(module_scope)
