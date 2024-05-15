from .DB import File, Tag, FileTag
from peewee import fn
from peewee import *

def SaveFile(file_name, file_content, *tags):
    # Verificar que el archivo no esta en la BD.
    tags_query = Tag.select(Tag.name).where(Tag.name in tags)
    tags_query_names = [tag.name for tag in tags_query]
    new_file = File.create(name=file_name, file_content=file_content)
    for tag in tags:
        if tag not in tags_query_names:
            tag = Tag.create(name=tag)
        else:
            tag = tags_query[tags_query_names.index(tag)]
        FileTag.create(file=new_file, tag=tag)

def AddTags(tags, *tag_query):
    files_query = RecoverFiles_ByTagQuery(tag_query)
    if len(files_query) <= 0:
        return -1
    for file_in_db in files_query:
        tags_query = Tag.select(Tag.name).join(FileTag).where(file=file_in_db)
        not_added_tags = filter(lambda tag: tag not in tags_query, tags)
        for tag_name in not_added_tags:
            existing_tag = Tag.get_or_none(name=tag_name)
            if not existing_tag:
                existing_tag = Tag.create(name=tag_name)
            FileTag.create(file=file_in_db, tag=existing_tag)
    return 1



def RecoverFiles_ByTagQuery(*tag_query:*str):
    # Obtener los archivos con TODOS los tags de la lista de tags: tag_query

    # 1. Hacer Join entre las 3 tablas
    # 2. Coger todas las tuplas de archivo-tag que tengan su tag en tag_query
    # 3. Agrupar por archivos y contar la cantidad de tuplas de dicho archivo que se recuperaron.
    # 4. Filtrar los que tienen la cantidad de tuplas igual a la cantidad de tuplas en tags_query.

    #! Verificar si sirve con el in como expresion normal de python
    #! Verificar si el primer COUNT se puede borrar.
    #! Verificar si sirve el nombrado del COUNT.
    query = Tag.select(File, fn.COUNT(File.id).alias('file_count')).join(FileTag).join(File).where(Tag.name.in_(tag_query)).group_by(File).having(file_count == len(tag_query))
    return query

        
