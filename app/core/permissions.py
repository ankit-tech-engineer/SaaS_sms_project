from enum import Enum
from typing import List

class Role(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    SUPPORT = "SUPPORT"

class Permission(str, Enum):
    MANAGE_PLANS = "MANAGE_PLANS"
    MANAGE_ORGS = "MANAGE_ORGS"
    VIEW_ANALYTICS = "VIEW_ANALYTICS"
    MANAGE_USERS = "MANAGE_USERS"

# Role defaults
ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN: [
        Permission.MANAGE_PLANS, 
        Permission.MANAGE_ORGS, 
        Permission.VIEW_ANALYTICS, 
        Permission.MANAGE_USERS
    ],
    Role.ADMIN: [
        Permission.MANAGE_ORGS,
        Permission.VIEW_ANALYTICS
    ]
}
