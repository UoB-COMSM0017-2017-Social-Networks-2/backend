class Region:
    def __init__(self, name, woeid, parent_name):
        self.name = name
        self.woeid = woeid
        self.parent_name = parent_name

    def get_parent(self):
        for region in all_regions:
            if region.name == self.parent_name:
                return region
        return None


all_regions = [
    Region("Scotland", 12578048, "United Kingdom"),
    Region("Bristol", 13963, "England"),
    Region("London", 44418, "England"),
    Region("United Kingdom", 23424975, None),
    Region("England", 24554868, "United Kingdom"),
    Region("Bath", 12056, "England"),
    Region("Cardiff", 15127, "Wales"),
    Region("Wales", 12578049, "United Kingdom")
]


def get_all_regions():
    return all_regions


def is_in_region(region, ancestor):
    if ancestor is None:
        return True
    if region is None:
        return False
    if region.woeid == ancestor.woeid:
        return True
    return is_in_region(region.get_parent(), ancestor)


def get_region_by_woeid(woeid):
    for region in all_regions:
        if region.woeid == woeid:
            return region
    return None


def get_global_region():
    return get_region_by_woeid(23424975)
