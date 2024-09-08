from .DB import get_File_Tag_DB
from peewee import fn
from peewee import *
from hashlib import sha1


class File_Tag_DB:
    def __init__(self, db_name:str):
        file_tag_DB = get_File_Tag_DB(db_name=db_name)
        self.DB = file_tag_DB[0]
        self.Tag = file_tag_DB[1]
        self.File = file_tag_DB[2]
        self.FileTag = file_tag_DB[3]
    
    def AddFiles(self, files, tags, location_hash):
        for (file_name, file_content) in files:
            self.SaveFile(file_name, file_content, location_hash, *tags)
    def AddLocalFiles(self, file_names, tags, location_hash):
        for file_name in file_names:
            with open(file_name, 'rb') as file:
                file_content = file.read()
                self.SaveFile(file_name, file_content, location_hash, *tags)

    def SaveFile(self, file_name, file_content, location_hash, *tags):
        """Salvar un archivo en la BD con determinadas etiquetas: tags"""
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        tags_query = Tag.select(Tag).where(Tag.name.in_(tags))
        tags_query_names = [tag.name for tag in tags_query]
        print(f"tag_query: {tags_query}")
        new_file = File.create(name=file_name, content=file_content, file_hash=sha1(file_content.encode('utf-8')), location_hash=location_hash)
        # Comprobando que cada uno de los tags esten en la BD
        for tag in tags:
            if tag not in tags_query_names:
                tag = Tag.create(name=tag)
            else:
                tag = tags_query[tags_query_names.index(tag)]
            # Asociando cada tag al archivo
            FileTag.create(file=new_file, tag=tag)


    def RecoverFilesNames_ByTagQuery(self, tag_query, arg2=None):
        """Obtener los archivos con TODOS los tags de la lista de tags: tag_query"""
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        query = (File
                    .select(File, fn.COUNT(Tag.id).alias('tag_count'))
                    .join(FileTag)
                    .join(Tag)
                    .where(Tag.name.in_(tag_query))
                    .group_by(File)
                    .having(fn.COUNT(Tag.id) == len(tag_query))).select(File.name)
        result = [item.name for item in query]
        return result
    def RecoveryFilesInfo_ByTagQuery(self, tag_query, include_tags=False):
        """Obtener información de identificacion unica de los archivos con TODOS los tags de la lista de tags: tag_query"""
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        query = (File
                    .select(File, fn.COUNT(Tag.id).alias('tag_count'), File.file_hash)
                    .join(FileTag)
                    .join(Tag)
                    .where(Tag.name.in_(tag_query))
                    .group_by(File)
                    .having(fn.COUNT(Tag.id) == len(tag_query)))
        result = ((item.name, item.file_hash, [tag.name for tag in item.tags]) for item in query)
        return result if include_tags else ((item[0], item[1]) for item in result)

    def RecoveryFileContent_ByInfo(self, file_hash):
        """Obtener el titulo, el contenido y los tags del archivo con el hash de archivo: file_hash"""
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        recovered_file = File.get(File.file_hash == file_hash)
        if len(result) == 0:
            print("No se encontro el archivo con ese hash")
            return None
        file_tags = (Tag
                        .select(Tag)
                        .join(FileTag)
                        .where(FileTag.file == recovered_file))
        return (recovered_file, [tag.name for tag in file_tags])
            
    def DeleteFiles(self, tag_query, arg2=None):
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        files_query = RecoverFilesNames_ByTagQuery(self, tag_query)
        delete_files_columns = File.delete().where(File.name.in_(files_query))
        delete_files_tags_columns = FileTag.delete().where(FileTag.file.in_(files_query))
        delete_files_columns.execute()
        delete_files_tags_columns.execute()

        print(f"se eliminaron las columnas: {files_query}")

    def AddTags(self, tag_query, tags):
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        files_query = RecoveryFilesInfo_ByTagQuery(self, tag_query)
        files_hashs = []
        for file in files_query:
            file_hash = file[1]
            files_hashs.append(file_hash)

        if len(files_hashs) == 0:
            print("Ningun elemento coincide con la consulta")
            return
        for file_in_db in files_hashs:
            # Tomar los tags que se van a añadir al archivo. Esto implica excluir los tags que ya estan asociados a cada archivo en la BD.
            file_tags = [tag.name for tag in Tag.select(Tag).join(FileTag).where(FileTag.file == file_in_db)]
            # Limpiar los tags que estan repetidos
            filtered_tags_to_add = filter(lambda tag: tag not in file_tags, tags)
            for tag_name in filtered_tags_to_add:
                existing_tag = Tag.get_or_none(name=tag_name)
                if not existing_tag:
                    existing_tag = Tag.create(name=tag_name)
                try:
                    FileTag.create(file=file_in_db, tag=existing_tag)
                except Exception as e:
                    return f"Parametros no validos: {e}"
                    
                
        return "Tags añadidas correctamente"



    def DeleteTags(self, tag_query, tags):
        """Desasocia los incluidos en tags de los archivos que cumplen con la tag query"""
        # Decidi mantener los tags que queden sin asociarse a ningun archivo para no tener que agregarlos en el futuro. Una estrategia real que se 
        # llevaria a cabo es liberar cada cierto tiempo la base de datos de tags que no son asociados hace tiempo a ningun archivo
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        files_query = RecoveryFilesInfo_ByTagQuery(self, tag_query)
        for _, file_hash in files_query:
            filtered_filetags_to_delete = [file_tag for file_tag in (FileTag
                                                                        .select(FileTag)
                                                                        .join(Tag)
                                                                        .where(FileTag.file == file_hash)
                                                                        .where(Tag.name.in_(tags)))]
            FileTag.delete().where(FileTag.id.in_(filtered_filetags_to_delete)).execute()
                