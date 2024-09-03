import csv
import datetime
import pathlib

import httpx
import zoneinfo
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from server.incidents.fields import PartialDate
from server.incidents.models import (
    Attachment,
    Extra,
    Incident,
    IncidentType,
    Region,
    School,
    SchoolDistrict,
    SourceType,
)

# NOTE WELL: this was a quickly written hack to import data from CSV files
# exported from AirTable. Hopefully once it works, and we import all the data,
# we can call it a day and never use it again. It's not meant to be pretty or
# efficient, just functional.


class Command(BaseCommand):
    """
    Command that loads contents from an exports directory.

    The directory must have three files: `schools.csv`, `incidents.csv`, and
    `districts.csv`.

    The command takes a single argument: the path to the exports directory.
    """

    def add_arguments(self, parser):
        parser.add_argument("path", type=str)

    def handle(self, *args, **options):
        # Get the path to the exports directory
        data_dir = pathlib.Path(options["path"]).resolve()

        # Load the districts
        districts_path = data_dir / "districts.csv"
        self.load_districts(districts_path)

        # Load the schools
        schools_path = data_dir / "schools.csv"
        self.load_schools(schools_path)

        # Load the incidents
        incidents_path = data_dir / "incidents.csv"
        self.load_incidents(incidents_path)

    def seattle(self) -> Region:
        """Get or create the Seattle region."""
        seattle, _ = Region.objects.get_or_create_with_group(name="Seattle")
        return seattle

    def publisher(self) -> User:
        """Get or create the default publisher user."""
        user = User.objects.get(pk=1)
        assert user.is_superuser
        return user

    def load_districts(self, path: pathlib.Path):
        """Load districts from a CSV file."""
        self.stdout.write(f"Loading districts from {path}")
        with open(path, encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row["District-Name"].strip()
                existing_district = SchoolDistrict.objects.filter(name=name).first()
                if existing_district:
                    self.stdout.write(f"District already exists: {existing_district}")
                    continue
                assert name
                logo_parts_str = row["District-Logo"].strip()
                logo_name, logo_url = logo_parts_str.split("(")
                logo_name = logo_name.strip()
                logo_url = logo_url.strip(")").strip()
                logo_attachment = Attachment.objects.create(
                    name=logo_name, data=httpx.get(logo_url).content
                )

                url = row["District-URL"].strip()
                assert url
                twitter = row["District-Twitter"].strip() or ""
                facebook = row["District-Facebook"].strip() or ""
                phone = row["District-Phone"].strip() or ""
                superintendent_name = row["Superintendent-Name"].strip()
                assert superintendent_name
                superintendent_email = row["Superintendent-Email"].strip()
                civil_rights_url = row["CivilRights-URL"].strip() or ""
                civil_rights_contact_name = row["CivilRights-Contact"].strip() or ""
                civil_rights_contact_email = row["CivilRights-Email"].strip() or ""
                hib_url = row["HIB-URL"].strip() or ""
                hib_form_url = row["HIB-Form"].strip() or ""
                hib_contact_name = row["HIB-Contact"].strip() or ""
                hib_contact_email = row["HIB-Email"].strip() or ""
                board_url = row["Board-URL"].strip() or ""

                district = SchoolDistrict.objects.create(
                    name=name,
                    url=url,
                    logo=logo_attachment,
                    twitter=twitter,
                    facebook=facebook,
                    phone=phone,
                    superintendent_name=superintendent_name,
                    superintendent_email=superintendent_email,
                    civil_rights_url=civil_rights_url,
                    civil_rights_contact_name=civil_rights_contact_name,
                    civil_rights_contact_email=civil_rights_contact_email,
                    hib_url=hib_url,
                    hib_form_url=hib_form_url,
                    hib_contact_name=hib_contact_name,
                    hib_contact_email=hib_contact_email,
                    board_url=board_url,
                )

                self.stdout.write(f"Created district: {district}")

    def load_schools(self, path: pathlib.Path):
        """Load schools from a CSV file."""
        self.stdout.write(f"Loading schools from {path}")
        with open(path, encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row["Name"].strip()
                assert name
                existing_school = School.objects.filter(name=name).first()
                if existing_school:
                    self.stdout.write(f"School already exists: {existing_school}")
                    continue
                url = row["Website"].strip()
                # assert url
                school_type = row["School-Type"].strip().lower()
                assert school_type in ["public", "private", ""]
                is_public = school_type == "public"
                school_district = row["District"].strip()
                district = (
                    SchoolDistrict.objects.get(name=school_district)
                    if school_district
                    else None
                )
                school_levels = [
                    sl.strip().lower() for sl in row["School-Level"].split(",")
                ]
                is_elementary = False
                is_middle = False
                is_high = False
                for school_level in school_levels:
                    if school_level == "elementary":
                        is_elementary = True
                    elif school_level == "middle":
                        is_middle = True
                    elif school_level == "high":
                        is_high = True
                address = row["Address"].strip()
                street = ""
                city = ""
                state = ""
                zip_code = ""
                if address:
                    address = address.replace("\n", " ")
                    comma_count = address.count(",")
                    # print(f"Address: {address}")
                    if comma_count == 2:
                        # How many parts to the state?
                        parts = address.split(",")
                        assert len(parts) == 3
                        street, city, state_zip = parts
                        street = street.strip()
                        city = city.strip()
                        state, zip_code = state_zip.strip().split(" ")
                        state = state.strip()
                        zip_code = zip_code.strip()
                    elif comma_count == 1:
                        # How many parts to the state?
                        parts = address.split(",")
                        try:
                            street_city, state_zip = parts
                            street_city = street_city.strip()
                            state, zip_code = state_zip.strip().split(" ")
                            state = state.strip()
                            zip_code = zip_code.strip()
                            street_city_parts = street_city.split(" ")
                            city = street_city_parts[-1]
                            street = " ".join(street_city_parts[:-1])
                            city = city.strip()
                            street = street.strip()
                        except Exception:
                            street, city_state_zip = parts
                            city_state_zip = city_state_zip.strip()
                            city, state, zip_code = city_state_zip.split(" ")
                            city = city.strip()
                            state = state.strip()
                            zip_code = zip_code.strip()
                            street = street.strip()
                    elif comma_count == 0:
                        parts = address.split(" ")
                        zip_code = parts[-1]
                        state = parts[-2]
                        city = parts[-3]  # What else can we do?
                        street = " ".join(parts[:-3])
                        zip_code = zip_code.strip()
                        state = state.strip()
                        city = city.strip()
                        street = street.strip()
                    else:
                        assert False, f"Unexpected address format: {address}"

                latitude_str = row["Latitude"].strip()
                longitude_str = row["Longitude"].strip()

                latitude = float(latitude_str) if latitude_str else None
                longitude = float(longitude_str) if longitude_str else None

                school = School.objects.create(
                    name=name,
                    url=url,
                    district=district,
                    street=street,
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    latitude=latitude,
                    longitude=longitude,
                    is_public=is_public,
                    is_elementary=is_elementary,
                    is_middle=is_middle,
                    is_high=is_high,
                )

                self.stdout.write(f"Created school: {school}")

    def load_incidents(self, path: pathlib.Path):
        """Load incidents from a CSV file."""
        self.stdout.write(f"Loading incidents from {path}")
        # NOTE: so far, all incidents are in Seattle
        region = self.seattle()
        # NOTE: so far, all incidents are published by the default user
        publisher = self.publisher()

        with open(path, encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row in reader:
                yyyy = row["Year"].strip()
                assert len(yyyy) == 4, f"Year: {yyyy}"
                mm = row["Month"].strip() or None
                assert mm is None or len(mm) == 2, f"Month: {mm}"
                dd = row["Day"].strip() or None
                if dd == "null":
                    dd = None
                assert dd is None or 1 <= len(dd) <= 2, f"Day: {dd}"
                occurred_at = PartialDate(
                    year=int(yyyy),
                    month=int(mm) if mm else None,
                    day=int(dd) if dd else None,
                )
                school_name = row["School"].strip()
                school = School.objects.get(name=school_name)
                incident_type_list = [
                    it.strip() for it in row["Incident-Type"].split(",")
                ]
                incident_types: list[IncidentType] = []
                for incident_type_name in incident_type_list:
                    incident_type, _ = IncidentType.objects.get_or_create(
                        name=incident_type_name
                    )
                    incident_types.append(incident_type)
                description = row["Incident-Description"].strip()

                supporting_materials: list[Attachment] = []

                supporting_materials_str = row["Supporting-Materials"].strip()
                if supporting_materials_str:
                    supporting_materials_parts = [
                        sm.strip() for sm in supporting_materials_str.split(",")
                    ]
                    for supporting_material in supporting_materials_parts:
                        supporting_material_name, supporting_material_url = (
                            supporting_material.split("(")
                        )
                        supporting_material_name = supporting_material_name.strip()
                        supporting_material_url = supporting_material_url.strip(
                            ")"
                        ).strip()
                        self.stdout.write(
                            f"Created supporting material: {supporting_material_name} ({supporting_material_url})"
                        )
                        supporting_material_response = httpx.get(
                            supporting_material_url
                        )
                        supporting_material_response.raise_for_status()
                        supporting_material = Attachment.objects.create(
                            name=supporting_material_name,
                            data=supporting_material_response.content,
                        )
                        supporting_materials.append(supporting_material)

                school_response = row["School-Response"].strip()

                extras: list[Extra] = []
                media_coverage = row["Media-Coverage"].strip()
                if media_coverage:
                    extra = Extra.objects.create(
                        name="media-coverage", value=media_coverage
                    )
                    extras.append(extra)

                social_media_post = row["Social-Media-Post"].strip()
                if social_media_post:
                    extra = Extra.objects.create(
                        name="social-media-post", value=social_media_post
                    )
                    extras.append(extra)

                other_related = row["Other-Related"].strip()
                if other_related:
                    extra = Extra.objects.create(
                        name="other-related", value=other_related
                    )
                    extras.append(extra)

                reported_school_str = row["Reported-School"].strip()
                reported_to_school = reported_school_str == "Yes"
                source_list = [s.strip() for s in row["Source(s)"].split(",")]
                source_types: list[SourceType] = []
                for source_name in source_list:
                    source_type, _ = SourceType.objects.get_or_create(name=source_name)
                    source_types.append(source_type)

                last_modified_str = row["Last Modified"].strip()
                # Parse date in format "M/DD/YYYY HH:MMam/pm"
                last_modified = datetime.datetime.strptime(
                    last_modified_str, "%m/%d/%Y %I:%M%p"
                )
                # Put it in the America/Los_Angeles timezone
                PACIFIC = zoneinfo.ZoneInfo("America/Los_Angeles")
                last_modified = last_modified.replace(tzinfo=PACIFIC)

                incident = Incident.objects.create(
                    region=region,
                    occurred_at=occurred_at,
                    school=school,
                    description=description,
                    reported_to_school=reported_to_school,
                    submitted_at=last_modified,  # Best we can do for now
                    published_at=last_modified,  # Best we can do for now
                    published_by=publisher,
                    school_response=school_response,
                )
                incident.incident_types.set(incident_types)
                incident.source_types.set(source_types)
                incident.supporting_materials.set(supporting_materials)

                self.stdout.write(f"Created incident: {incident}")
