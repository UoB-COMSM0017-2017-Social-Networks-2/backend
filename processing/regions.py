import json

from shapely.geometry import Point, shape


class Region:
    """
    The region id is {level}_{id}, as some IDs appear in level 1 and 2.
    """

    def __init__(self, name, region_id, parent_id):
        self.name = name
        self.region_id = region_id
        self.parent_id = parent_id
        self.shape = None
        self.nb_leaf_descendants = None
        self.leaf = None
        self.sub_region_ids = None

    def set_shape(self, region_shape):
        self.shape = region_shape

    def has_shape(self):
        return self.shape is not None

    def contains_point(self, point):
        if not self.has_shape():
            return False
        return self.shape.contains(point)

    def get_parent(self):
        for region in get_all_regions():
            if region.region_id == self.parent_id:
                return region
        return None

    def get_number_of_leaf_descendants(self):
        if self.nb_leaf_descendants is None:
            self.nb_leaf_descendants = len(
                list(filter(lambda r: r.is_leaf(), map(get_region_by_id, self.get_all_sub_region_ids()))))
        return self.nb_leaf_descendants

    def get_all_sub_region_ids(self):
        if self.sub_region_ids is None:
            self.sub_region_ids = set()
            for region in get_all_regions():
                if is_in_region(region, get_region_by_id(self.region_id)):
                    self.sub_region_ids.add(region.region_id)
        return set(self.sub_region_ids)

    def get_ancestors(self):
        res = []
        current = self.get_parent()
        while current is not None:
            res.append(current)
            current = current.get_parent()
        return res

    def is_leaf(self):
        if self.leaf is None:
            self.leaf = not any(region.parent_id == self.region_id for region in get_all_regions())
        return self.leaf


all_regions_dict = dict()


def load_regions():
    global all_regions_dict
    all_regions_dict = dict()
    with open('data/GBR_GeoJSON.json', 'r', encoding="utf-8") as f:
        gbr_data = json.load(f)
        regions_data = gbr_data["features"]
        for region_data in regions_data:
            properties = region_data["properties"]
            ids = []
            names = []
            leaf_id = None
            for i in range(10):
                name_key = "NAME_{}".format(i)
                id_key = "ID_{}".format(i)
                if name_key not in properties or id_key not in properties:
                    if name_key in properties or id_key in properties:
                        print("#ids != #names")
                    break
                names.append(properties[name_key])
                leaf_id = "{}_{}".format(i, properties[id_key])
                ids.append(leaf_id)

            prev_region_id = None
            for name, region_id in zip(names, ids):
                if region_id not in all_regions_dict:
                    region = Region(name, region_id, prev_region_id)
                    all_regions_dict[region_id] = region
                prev_region_id = region_id

            all_regions_dict[leaf_id].set_shape(shape(region_data['geometry']))


if len(all_regions_dict) == 0:
    load_regions()


def get_all_regions():
    return all_regions_dict.values()


def is_in_region(region, ancestor):
    if ancestor is None:
        return True
    if region is None:
        return False
    if region.region_id == ancestor.region_id:
        return True
    return is_in_region(region.get_parent(), ancestor)


def get_region_by_id(region_id):
    if region_id not in all_regions_dict:
        return None
    return all_regions_dict[region_id]


def get_global_region():
    return get_region_by_id("0_242")


# Function that returns region name based on input data
def get_smallest_region_by_coordinates(longitude, latitude):
    point = Point(longitude, latitude)
    containing_region = None
    for region in get_all_regions():
        if region.has_shape() and region.contains_point(point):
            if is_in_region(region, containing_region):
                containing_region = region
    return containing_region
