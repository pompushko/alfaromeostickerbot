import os
from peewee_aio import Manager, AIOModel, fields

db_file_loc = os.getenv("SQLITE_LOCATION") or "VINSpecLists.sqlite3"
conn = f"aiosqlite:///{db_file_loc}"

class SpecListMessages(AIOModel):
    _manager = Manager(conn)
    vin = fields.TextField(primary_key=True, null=False)
    msg_id = fields.TextField(null=True)
    
    class Meta:
        table_name = "SpecList_messages"
        

    

class AsyncDbHandler:
    def __init__(self):
        self.db_model = SpecListMessages()

    
    async def init_async(self):
        await self.db_model.create_table()

    async def AddVIN(self, vin: str, msg_id: [str, None] ):
        await self.db_model.create(
            vin=vin, 
            msg_id=msg_id
        )

    async def GetMessageIdByVin(self, vin: str) -> [str, None]:
        result = await self.db_model.get_or_none(vin=vin)
        if result:
            msg_id = result.msg_id
        else:
            msg_id = result
        return msg_id
   
    async def DeleteVin(self, vin: str):
        await self.db_model.delete_by_id(vin)

    async def UpdateMessageId(self, vin: str, msg_id: [str, None]):
        await self.db_model.update(msg_id=msg_id).where(self.db_model.vin == vin).execute()        