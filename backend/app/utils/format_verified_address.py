import usaddress


class FormattedAddress:
    address_line1: str | None
    address_line2: str | None
    city: str | None
    state: str | None
    zip: str | None


def format_verified_address(verified_address: str) -> FormattedAddress:
    components, _key = usaddress.tag(verified_address)  # components is an OrderedDict

    line1_parts = [
        components.get("AddressNumber"),
        components.get("StreetNamePreDirectional"),
        components.get("StreetName"),
        components.get("StreetNamePostType"),
        components.get("StreetNamePostDirectional"),
    ]
    street = " ".join(p for p in line1_parts if p).strip()

    address_line1 = street or None

    line2_parts = [
        components.get("OccupancyType"),
        components.get("OccupancyIdentifier"),
        components.get("SubaddressType"),
        components.get("SubaddressIdentifier"),
        components.get("BuildingName"),
    ]
    address_line2 = " ".join(p for p in line2_parts if p).strip() or None

    return {
        "address_line1": address_line1,
        "address_line2": address_line2,
        "city": components.get("PlaceName"),
        "state": components.get("StateName"),
        "zip": components.get("ZipCode"),
    }
