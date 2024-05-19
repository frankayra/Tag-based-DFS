from .DB import File, Tag, FileTag
from peewee import fn
from peewee import *

def AddFiles(files, tags):
    for file_name in files:
        # TODO manejo de errores
        with open(file_name, 'rb') as file:
            file_content = file.read()
            SaveFile(file_name, file_content, *tags)

def SaveFile(file_name, file_content, *tags):
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
    # Obtener los archivos con TODOS los tags de la lista de tags: tag_query

    # 1. Hacer Join entre las 3 tablas
    # 2. Coger todas las tuplas de archivo-tag que tengan su tag en tag_query
    # 3. Agrupar por archivos y contar la cantidad de tuplas de dicho archivo que se recuperaron.
    # 4. Filtrar los que tienen la cantidad de tuplas igual a la cantidad de tuplas en tags_query.

    #! Verificar si sirve con el in como expresion normal de python
    #! Verificar si el primer COUNT se puede borrar.
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
        # print(f"tag_query: {file_tags}")    # DEBUG
        # print(f"tags: {tags}")              # DEBUG
        # print(f"filtered tags: [",end="")   # DEBUG
        for tag_name in filtered_tags_to_add:
            # print(tag_name,end=" ")         # DEBUG
            existing_tag = Tag.get_or_none(name=tag_name)
            if not existing_tag:
                existing_tag = Tag.create(name=tag_name)
            try:
                FileTag.create(file=file_in_db, tag=existing_tag)
            except Exception as e:
                return f"Parametros no validos: {e}"
        # print("]")                          # DEBUG
                
            
    return "Tags añadidas correctamente"



def DeleteTags(tag_query, tags):
    files_query = RecoverFiles_ByTagQuery(tag_query)
    print(f"files match in DB: {files_query}")
    print(f"tags to delete(raw query): {tags}")
    for file_name in files_query:
        filtered_filetags_to_delete = [file_tag for file_tag in FileTag.select(FileTag).join(Tag).where(FileTag.file == file_name).where(Tag.name.in_(tags))]
        print(f"tags to delete for {file_name}(filtered): {filtered_filetags_to_delete}")
        FileTag.delete().where(FileTag.id.in_(filtered_filetags_to_delete)).execute()
            

        

# TODO Quitar la unicidad del nombre en la tabla File
# TODO Arreglar la dependencia en el codigo de la unicidad del nombre en la tabla File
# TODO Cambiar la llave primaria de File
# TODO Arreglar la dependencia en el codigo con el formato de la llave primaria de File, principalmente en la referenciacion desde FileTag

#### Queries de prueba ####
# add texto.txt|texto2.txt|texto3.txt fotos_con_mi_madre|vacaciones|viajes|playa|familia
# delete felicidad
# add-tags familia|vacaciones felicidad
# add-tags familia|vacaciones felicidad|disfrute
# delete felicidad
# list familia|vacaciones
# delete-tags familia|vacaciones felicidad
# list familia|vacaciones|felicidad 
# list familia
# delete familia
# list disfrute
# delete familia|Juaquin