from django.contrib.auth.models import Group

ROLE_PROBOSZCZ  = "Proboszcz"
ROLE_WIKARIUSZ  = "Wikariusz"
ROLE_SEKRETARIAT = "Sekretariat"

def user_in_group(user, group_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=group_name).exists()
