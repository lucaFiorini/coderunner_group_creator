
# Base data:
# Student ID
# States:
#   Student writes the following string as an answer: <GroupName> <Password>
#   System then:
#   Creates group if it doesn't exist
#   If the group exists, it checks if the password matches and adds the student to the group .
#   
#   If a student is alrady in a different group, then the system will remove them from the previous group and try to add them to the next group
#   num_rows num_columns column_headers 
import portalocker
from enum import Enum,auto       
from pydantic import BaseModel,TypeAdapter
from dataclasses import dataclass
import json

@dataclass
class Ok[T]:
    val : T

@dataclass
class Err[T]:
    val : T

type Result[OkT,ErrT] = Ok[OkT]|Err[ErrT]

class Group[MemberIDType](BaseModel):
    name: str
    members: list[MemberIDType]
    password: str

@dataclass
class GroupManager[MemberIDType]:
    source : str
    
    def __init__(self,source : str):
        self.source = source
        
    def get_data(self):
        with open(self.source) as f:
            return TypeAdapter(list[Group[MemberIDType]]).validate_json(f.read())

    class AddError(Enum):
        GROUP_NOT_FOUND = auto()
        WRONG_PASSWORD = auto()
    
    def register(self, group_name : str, group_password : str, member_id : MemberIDType) -> Result[None,AddError]:
        with portalocker.Lock(self.source,'r+') as f:
                      
            group_data = self.get_data()            
            add_error : None|GroupManager.AddError = None
            
            group_exists = False
            for group in group_data:
                if member_id in group.members:
                    group.members.remove(member_id)
                if group.name == group_name:
                    #Group found, add user to group
                    group_exists = True
                    if group.password == group_password:
                        group.members.append(member_id)
                    else:
                        add_error = GroupManager.AddError.WRONG_PASSWORD

            if not group_exists:
                #Group not found, create group
                group_data.append(Group(
                    name=group_name,
                    password=group_password,
                    members=[member_id]
                ))

            #Update file
            f.write([group.model_dump() for group in group_data])
            
            #Return files
            if add_error != None:
                return Err(add_error)
            else:
                return Ok(None)
             
        return Ok(None)