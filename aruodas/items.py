# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import MapCompose, TakeFirst
from scrapy.loader import ItemLoader
from w3lib.html import remove_tags


def del_unwanted_features(features_dict):
    # used for removing unwanted features like advertisement feature
    unwanted_features = ["reklama"]
    for k in features_dict.copy():
        if any([feature in k.lower() for feature in unwanted_features]):
            features_dict.pop(k, None)
    return features_dict

def fix_sq_m(features_dict):
    # used for removing m² and replacing , to .
    feature_kw = "plotas"
    for k in features_dict:
        if feature_kw in k.lower():
            features_dict[k] = features_dict[k].replace("m²", "").replace(",", ".").strip()
    return features_dict

def fix_images(val):
    # used for removing all vals which are not urls
    if val.startswith("http"):
        return val

def fix_price(val):
    # used for removing € and any blank spaces
    chars_to_remove = ["€", " "]
    for char in chars_to_remove:
        val = val.replace(char, "")
    return val.strip()

def fix_price_per_sq_m(val):
    # used for removing ()€m²/ any blank spaces
    chars_to_remove = ["€", "(", ")", "m²", "/", " "]
    for char in chars_to_remove:
        val = val.replace(char, "")
    return val.strip()

def take_last_elem(values):
    for value in values[::-1]:
        if value is not None and value != "":
            return remove_tags(value)

class AruodasItem(scrapy.Item):
    datetime = scrapy.Field(output_processor=TakeFirst())
    url = scrapy.Field(output_processor=TakeFirst())
    street = scrapy.Field(input_processor=take_last_elem, output_processor=TakeFirst())
    header = scrapy.Field(input_processor=MapCompose(remove_tags, lambda v: v.strip()), output_processor=TakeFirst())
    images = scrapy.Field(input_processor=MapCompose(fix_images))
    price = scrapy.Field(input_processor=MapCompose(remove_tags, fix_price), output_processor=TakeFirst())
    price_per_sq_m = scrapy.Field(input_processor=MapCompose(remove_tags, fix_price_per_sq_m), output_processor=TakeFirst())
    features = scrapy.Field(input_processor=MapCompose(del_unwanted_features, fix_sq_m), output_processor=TakeFirst())
    description = scrapy.Field(output_processor=TakeFirst())
    seller_phone_num = scrapy.Field(input_processor=MapCompose(remove_tags), output_processor=TakeFirst())
    seller_url = scrapy.Field(output_processor=TakeFirst())
    stats = scrapy.Field(output_processor=TakeFirst())
