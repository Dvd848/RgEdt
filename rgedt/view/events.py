import enum

class Events(enum.Enum):
    KEY_SELECTED = enum.auto()
    EDIT_VALUE   = enum.auto()
    ADD_KEY      = enum.auto()
    ADD_VALUE    = enum.auto()
    DELETE_VALUE = enum.auto()
    REFRESH      = enum.auto()
    SET_STATUS   = enum.auto()
    SHOW_ERROR   = enum.auto()