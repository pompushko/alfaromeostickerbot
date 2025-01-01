from peewee import *
import os

db_file_loc = os.getenv("SQLITE_LOCATION") or "VINComplectations.sqlite3"
conn = SqliteDatabase(db_file_loc)

class ComplectationFiles(Model):
    vin_field = TextField(column_name='VIN', primary_key=True)
    pdf_blob = BlobField(column_name='PDF_File', null=True)

    class Meta:
        table_name = "Complectation_files"
        database = conn
        
class DbHandler():
    
    def __init__(self ):
        self.db_model = ComplectationFiles()
        tables = self.db_model._meta.database.get_tables()
        if "Complectation_files" not in tables:
            self.__init_schema()
        
    def __init_schema(self):
        self.db_model._meta.database.create_tables([self.db_model])
        
    def AddFile(self, vin: str, opened_file: bytes):
        self.db_model.create(vin_field = vin, pdf_blob = opened_file)

    def GetFileByVin(self, vin: str ) -> bytes:
        try: 
            blob = self.db_model.get_by_id(vin).pdf_blob
        except DoesNotExist as e:
            blob = "File not found"
        return blob
        

