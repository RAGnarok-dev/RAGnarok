from enum import IntEnum


class PermissionType(IntEnum):
    READ = 1
    WRITE = 2
    ADMIN = 3


class PrincipalType(IntEnum):
    USER = 1
    TENANT = 10
