from peewee import *

# Configuración de la base de datos



def get_File_Tag_DB(db_name:str):
    """Base de datos para tener archivos asociados con sus tags"""

    db = SqliteDatabase(f'{db_name}.db')

    class BaseModel(Model):
        class Meta:
            database = db
    class File(BaseModel):
        file_hash = CharField(primary_key=True)
        name = CharField()
        content = BlobField()
        location_hash = IntegerField(constraints=[Check('location_hash >= 0')])
        
    class Tag(BaseModel):
        name = CharField(unique=True)  # Convierte en unico el campo 'name' en la tabla

    class FileTag(BaseModel):
        file = ForeignKeyField(File, backref='tags', on_delete='CASCADE')
        tag = ForeignKeyField(Tag, backref='files', on_delete='CASCADE')
        class Meta:
            # Debemos incluir database = db aqui porque estamos sobrescribiendo Meta
            database = db
            indexes = (
                (('file', 'tag'), True),  # Indica la unicidad de la tupla (file, tag) en la tabla.
            )
    db.connect()
    db.create_tables([File, Tag, FileTag])
    return db, File, Tag, FileTag


