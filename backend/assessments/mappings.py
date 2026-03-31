from assets.models import LoadCapacity

# equipment_type → (capacity_name, metric, user-facing label)
EQUIPMENT_CAPACITY_MAP = {
    "crane_with_outriggers":  (LoadCapacity.CapacityName.MAX_POINT_LOAD,               "kN",  "Max Outrigger Load"),
    "mobile_crane":           (LoadCapacity.CapacityName.MAX_AXLE_LOAD,                "t",   "Max Axle Load"),
    "heavy_vehicle":          (LoadCapacity.CapacityName.MAX_AXLE_LOAD,                "t",   "Max Axle Load"),
    "elevated_work_platform": (LoadCapacity.CapacityName.MAX_POINT_LOAD,               "kN",  "Max Wheel Load"),
    "storage_load":           (LoadCapacity.CapacityName.MAX_UNIFORM_DISTRIBUTOR_LOAD, "kPa", "Uniform Distributor Load"),
    "vessel":                 (LoadCapacity.CapacityName.MAX_DISPLACEMENT_SIZE,        "t",   "Displacement"),
}