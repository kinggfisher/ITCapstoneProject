from assets.models import LoadCapacity

# Maps equipment_type → (capacity_name, load_label)
# capacity_name: used to query LoadCapacity from database
# load_label: user-facing label (e.g. "Max Outrigger Load" vs "Max Wheel Load")
#
# CHANGED: metric removed from mapping — fetched from LoadCapacity.metric at runtime
# instead of being hardcoded here. This ensures metric is always consistent
# with what's stored in the database.
#
# TODO: If admin needs to manage equipment types without code changes,
# migrate this mapping to an EquipmentCapacityMapping database table
# and register it in Django Admin.
#
# TODO: If equipment-capacity mapping is available from client's external
# data source or API, replace this hardcoded map with a sync mechanism.

EQUIPMENT_CAPACITY_MAP = {
    "crane_with_outriggers":  (LoadCapacity.CapacityName.MAX_POINT_LOAD,               "Max Outrigger Load"),
    "mobile_crane":           (LoadCapacity.CapacityName.MAX_AXLE_LOAD,                "Max Axle Load"),
    "heavy_vehicle":          (LoadCapacity.CapacityName.MAX_AXLE_LOAD,                "Max Axle Load"),
    "elevated_work_platform": (LoadCapacity.CapacityName.MAX_POINT_LOAD,               "Max Wheel Load"),
    "storage_load":           (LoadCapacity.CapacityName.MAX_UNIFORM_DISTRIBUTOR_LOAD, "Uniform Distributor Load"),
    "vessel":                 (LoadCapacity.CapacityName.MAX_DISPLACEMENT_SIZE,        "Displacement"),
}