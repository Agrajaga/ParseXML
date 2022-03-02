from xml.etree import cElementTree as ET


def descript_flight(flight: ET.Element) -> dict:
    flight_desc = {}
    flight_desc["Carrier_id"] = flight.find("Carrier").get("id")
    for flight_attrib in flight:
        if flight_attrib.tag == "FareBasis":
            continue
        flight_desc[flight_attrib.tag] = flight_attrib.text
    return flight_desc


if __name__ == "__main__":
    tree = ET.parse("RS_Via-3.xml")
    root = tree.getroot()

    variants = []
    for variant in root.findall("./PricedItineraries/Flights"):
        variant_desc = {}
        flight_desc = {}

        variant_desc["FareBasis"] = variant.find(
            "OnwardPricedItinerary/Flights/Flight/FareBasis").text

        variant_desc["onward"] = []
        for flight in variant.findall("OnwardPricedItinerary/Flights/Flight"):
            variant_desc["onward"].append(descript_flight(flight))

        variant_desc["return"] = []
        for flight in variant.findall("ReturnPricedItinerary/Flights/Flight"):
            variant_desc["return"].append(descript_flight(flight))

        variants.append(variant_desc)

    print(variants)
