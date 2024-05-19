from peewee import *

# Configuración de la base de datos

db = SqliteDatabase('files.db')

class BaseModel(Model):
    class Meta:
        database = db

class File(BaseModel):
    name = CharField(primary_key=True)
    file_content = BlobField()

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

# Crear las tablas
def StartDB():
    db.connect()
    db.create_tables([File, Tag, FileTag])
    return db


