from .DB import File, Tag, FileTag
from peewee import fn
from peewee import *

def AddFiles(files, tags):
    for file_name in files:
        with open(file_name, 'rb') as file:
            file_content = file.read()
            SaveFile(file_name, file_content, *tags)

def SaveFile(file_name, file_content, *tags):
    """Salvar un archivo en la BD con determinadas etiquetas: tags"""
    tags_query = Tag.select(Tag).where(Tag.name.in_(tags))
    tags_query_names = [tag.name for tag in tags_query]
    print(f"tag_query: {tags_query}")
    new_file = File.create(name=file_name, file_content=file_content)
    # Comprobando que cada uno de los tags esten en la BD
    for tag in tags:
        if tag not in tags_query_names:
            tag = Tag.create(name=tag)
        else:
            tag = tags_query[tags_query_names.index(tag)]
        # Asociando cada tag al archivo
        FileTag.create(file=new_file, tag=tag)


def RecoverFiles_ByTagQuery(tag_query, arg2=None):
    """Obtener los archivos con TODOS los tags de la lista de tags: tag_query"""

    query = (File
                .select(File, fn.COUNT(Tag.id).alias('tag_count'))
                .join(FileTag)
                .join(Tag)
                .where(Tag.name.in_(tag_query))
                .group_by(File)
                .having(fn.COUNT(Tag.id) == len(tag_query))).select(File.name)
    result = [item.name for item in query]
    return result
        
def DeleteFiles(tag_query, arg2=None):
    files_query = RecoverFiles_ByTagQuery(tag_query)
    delete_files_columns = File.delete().where(File.name.in_(files_query))
    delete_files_tags_columns = FileTag.delete().where(FileTag.file.in_(files_query))
    delete_files_columns.execute()
    delete_files_tags_columns.execute()

    print(f"se eliminaron las columnas: {files_query}")

def AddTags(tag_query, tags):
    files_query = RecoverFiles_ByTagQuery(tag_query)

    if len(files_query) == 0:
        print("Ningun elemento coincide con la consulta")
        return
    for file_in_db in files_query:
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



def DeleteTags(tag_query, tags):
    files_query = RecoverFiles_ByTagQuery(tag_query)
    for file_name in files_query:
        filtered_filetags_to_delete = [file_tag for file_tag in FileTag.select(FileTag).join(Tag).where(FileTag.file == file_name).where(Tag.name.in_(tags))]
        FileTag.delete().where(FileTag.id.in_(filtered_filetags_to_delete)).execute()
            