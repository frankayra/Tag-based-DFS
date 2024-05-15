from peewee import *

# Configuración de la base de datos
db = SqliteDatabase('files.db')

class BaseModel(Model):
    class Meta:
        database = db

class File(BaseModel):
    name = CharField()
    file_content = BlobField()

class Tag(BaseModel):
    name = CharField(unique=True)  # Crear índice unico en la columna 'name'

class FileTag(BaseModel):
    file = ForeignKeyField(File, backref='tags')
    tag = ForeignKeyField(Tag, backref='files')

# Crear las tablas
db.connect()
db.create_tables([File, Tag, FileTag])


