import json


class Region:
    """
    The region id is {level}_{id}, as some IDs appear in level 1 and 2.
    """

    def __init__(self, name, region_id, parent_id):
        self.name = name
        self.region_id = region_id
        self.parent_id = parent_id

    def get_parent(self):
        for region in all_regions_dict.values():
            if region.id == self.parent_id:
                return region
        return None


all_regions_dict = dict()


def load_regions():
    global all_regions_dict
    all_regions_dict = dict()
    with open('Coordinates2Region/GBR_GeoJSON.json') as file:
        gbr_data = json.load(file)
        regions_data = gbr_data["features"]
        for region_data in regions_data:
            properties = region_data["properties"]
            ids = []
            names = []
            for i in range(10):
                name_key = "NAME_{}".format(i)
                id_key = "ID_{}".format(i)
                if name_key not in properties or id_key not in properties:
                    if name_key in properties or id_key in properties:
                        print("#ids != #names")
                    break
                names.append(properties[name_key])
                ids.append("{}_{}".format(i, properties[id_key]))

            prev_region_id = None
            for name, region_id in zip(names, ids):
                if region_id not in all_regions_dict:
                    region = Region(name, region_id, prev_region_id)
                    all_regions_dict[region_id] = region
                prev_region_id = region_id


if len(all_regions_dict) == 0:
    load_regions()


def get_all_regions():
    return all_regions_dict.values()


def is_in_region(region, ancestor):
    if ancestor is None:
        return True
    if region is None:
        return False
    if region.id == ancestor.id:
        return True
    return is_in_region(region.get_parent(), ancestor)


def get_region_by_id(region_id):
    if region_id not in all_regions_dict:
        return None
    return all_regions_dict[region_id]


def get_global_region():
    return get_region_by_id("0_242")
