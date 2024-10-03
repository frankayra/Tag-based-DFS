from .DB import get_File_Tag_DB, get_File_Reference_DB
from peewee import fn
from peewee import *
from hashlib import sha1


class File_Tag_DB:
    def __init__(self, db_name:str):
        file_tag_DB = get_File_Tag_DB(db_name=db_name)
        self.DB = file_tag_DB[0]
        self.File = file_tag_DB[1]
        self.Tag = file_tag_DB[2]
        self.FileTag = file_tag_DB[3]
    
    def AddFiles(self, files, tags, location_hash):
        message = "\n\n"
        for (file_name, file_content) in files:
            operation_message, error = self.SaveFile(file_name, file_content, location_hash, *tags)
            if not error:
                message += f"{file_name} ✅: {operation_message}"
            else:
                message += f"{file_name} ❌: {operation_message}"
        return message
    def AddLocalFiles(self, file_names, tags, location_hash):
        for file_name in file_names:
            with open(file_name, 'rb') as file:
                file_content = file.read()
                self.SaveFile(file_name, file_content, location_hash, *tags)

    def SaveFile(self, file_name, file_content, location_hash, *tags) -> tuple[str, bool]:
        """Salvar un archivo en la BD con determinadas etiquetas: tags"""
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        log = "\nLog:\n"
        
        # File
        file_hash = sha1(file_content.encode('utf-8')).hexdigest()
        file_in_db = File.get_or_none(File.file_hash == file_hash)
        if file_in_db:
            return f"El archivo '{file_in_db.name}' ya estaba en la base de datos\n", True
        new_file = File.create(name=file_name, content=file_content, file_hash=file_hash, location_hash=location_hash)

        # Tags
        tags_in_db = Tag.select(Tag).where(Tag.name.in_(tags))
        def find_tag_in_db(tag):
            for tagg in tags_in_db:
                if tagg.name == tag: return tagg
            return None
        # Comprobando que cada uno de los tags esten en la BD
        for tag in tags:
            tag_in_DB = find_tag_in_db(tag)
            if not tag_in_DB:
                tag = Tag.create(name=tag)
                log += f"Tag '{tag.name}' creada 🔖\n"
            else:
                tag = tag_in_DB
            # Asociando cada tag al archivo
            file_tag_in_DB = FileTag.get_or_none((FileTag.file == new_file) & (FileTag.tag == tag))
            if file_tag_in_DB:
                log += "La tabla FileTag no esta consistente, se encontro una referencia ya existente a un archivo que no habia sido añadido.\n"
            else:

                try:
                    FileTag.create(file=new_file, tag=tag)
                except Exception as e:
                    return log + f"Error al salvar el archivo: {e}\n", True
        return log, False
 

    def RecoverFilesNames_ByTagQuery(self, tag_query, arg2=None):
        """Obtener los archivos con TODOS los tags de la lista de tags: tag_query"""
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        query = (File
                    .select(File, fn.COUNT(Tag.id).alias('tag_count'))
                    .join(FileTag)
                    .join(Tag)
                    .where(Tag.name.in_(tag_query))
                    .group_by(File)
                    .having(fn.COUNT(Tag.id) == len(tag_query)))
        result = [item.name for item in query]
        return result
    def RecoveryFilesInfo_ByTagQuery(self, tag_query, include_tags=False):
        """Obtener información de identificacion unica de los archivos con TODOS los tags de la lista de tags: tag_query"""
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        query = (File
                    .select(File, fn.COUNT(Tag.id).alias('tag_count'))
                    .join(FileTag)
                    .join(Tag)
                    .where(Tag.name.in_(tag_query))
                    .group_by(File)
                    .having(fn.COUNT(Tag.id) == len(tag_query)))
        result = ((item.name, item.file_hash, item.location_hash, [file_tag.tag.name for file_tag in item.tags]) for item in query)
        return result if include_tags else ((item[0], item[1]) for item in result)

    def RecoveryFileContent_ByInfo(self, file_hash):
        """Obtener el titulo, el contenido y los tags del archivo con el hash de archivo: file_hash"""
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        recovered_file = File.get_or_none(File.file_hash == file_hash)
        if not recovered_file:
            print("No se encontro el archivo con ese hash")
            return None
        return recovered_file
            
    def DeleteFiles(self, tag_query, arg2=None):
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        files_query = self.RecoverFilesNames_ByTagQuery(tag_query)
        delete_files_columns = File.delete().where(File.name.in_(files_query))
        delete_files_tags_columns_subquery = [file_tag for file_tag in FileTag.select(FileTag).join(File).where(File.name.in_(files_query))]
        delete_files_tags_columns_query = FileTag.delete().where(FileTag.id.in_(delete_files_tags_columns_subquery))

        delete_files_columns.execute()
        delete_files_tags_columns_query.execute()

        return f"Se eliminaron los archivos: {files_query}"

    def AddTags(self, tag_query, tags):
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        files_query = self.RecoveryFilesInfo_ByTagQuery(tag_query)
        files_hashs = []
        for file in files_query:
            file_hash = file[1]
            files_hashs.append(file_hash)

        if len(files_hashs) == 0:
            return "Ningun elemento coincide con la consulta"
        for file_in_db in files_hashs:
            # Tomar los tags que se van a añadir al archivo. Esto implica excluir los tags que ya estan asociados a cada archivo en la BD.
            file_tags = [tag.name for tag in Tag.select(Tag).join(FileTag).where(FileTag.file == file_in_db)]
            # Limpiar los tags que ya tenia el archivo.
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
        files_query = self.RecoveryFilesInfo_ByTagQuery(tag_query)
        for _, file_hash in files_query:
            filtered_filetags_to_delete = [file_tag for file_tag in (FileTag
                                                                        .select(FileTag)
                                                                        .join(Tag)
                                                                        .where(FileTag.file == file_hash)
                                                                        .where(Tag.name.in_(tags)))]
            FileTag.delete().where(FileTag.id.in_(filtered_filetags_to_delete)).execute()
                
class Files_References_DB(File_Tag_DB):
    def __init__(self, db_name:str):
        file_tag_DB = get_File_Reference_DB(db_name=db_name)
        self.DB = file_tag_DB[0]
        self.File = file_tag_DB[1]
        self.Tag = file_tag_DB[2]
        self.FileTag = file_tag_DB[3]

    def AddFiles(self, files, tags, location_hash):
        message = "\n\n"
        for (file_name, file_hash) in files:
            operation_message, error = self.SaveFile(file_name, file_hash, location_hash, *tags)
            if not error:
                message += f"{file_name} ✅: {operation_message}"
            else:
                message += f"{file_name} ❌: {operation_message}"
        return message
    def SaveFile(self, file_name, file_hash, location_hash, *tags) -> tuple[str, bool]:
        """Salvar la referencia a un archivo en la BD con determinadas etiquetas: tags"""
        File, Tag, FileTag = self.File, self.Tag, self.FileTag
        log = "\nLog:\n"
        
        # File
        file_in_db = File.get_or_none(File.file_hash == file_hash)
        if file_in_db:
            return f"El archivo '{file_in_db.name}' ya estaba en la base de datos\n", True
        new_file = File.create(name=file_name, file_hash=file_hash, location_hash=location_hash)

        # Tags
        tags_in_db = Tag.select(Tag).where(Tag.name.in_(tags))
        def find_tag_in_db(tag):
            for tagg in tags_in_db:
                if tagg.name == tag: return tagg
            return None
        # Comprobando que cada uno de los tags esten en la BD
        for tag in tags:
            tag_in_DB = find_tag_in_db(tag)
            if not tag_in_DB:
                tag = Tag.create(name=tag)
                log += f"Tag '{tag.name}' creada 🔖\n"
            else:
                tag = tag_in_DB
            # Asociando cada tag al archivo
            file_tag_in_DB = FileTag.get_or_none((FileTag.file == new_file) & (FileTag.tag == tag))
            if file_tag_in_DB:
                log += "La tabla FileTag no esta consistente, se encontro una referencia ya existente a un archivo que no habia sido añadido.\n"
            else:

                try:
                    FileTag.create(file=new_file, tag=tag)
                except Exception as e:
                    return log + f"Error al salvar el archivo: {e}\n", True
        return log, False
    def RecoveryFileContent_ByInfo(self, file_hash): 
        raise Exception("Se intento recuperar el contenido de un archivo en una base de datos de referencias solamente")