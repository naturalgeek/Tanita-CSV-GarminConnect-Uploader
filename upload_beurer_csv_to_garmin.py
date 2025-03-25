#!/usr/bin/env python3
import csv
import logging
import os
import sys
from datetime import datetime
from getpass import getpass

import requests
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)
from garth.exc import GarthHTTPError

# Configure debug logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = None


def get_credentials():
    """Get user credentials."""

    email = input("Login e-mail: ")
    password = getpass("Enter password: ")

    return email, password


def get_mfa():
    """Get MFA."""

    return input("MFA one-time code: ")


def init_api(first_name):
    """Initialize Garmin API with your credentials."""

    tokenstore = os.getenv("GARMINTOKENS") or f"~/.garminconnect.{first_name}"
    tokenstore_base64 = (
        os.getenv("GARMINTOKENS_BASE64") or f"~/.garminconnect_base64.{first_name}"
    )

    try:
        # Using Oauth1 and OAuth2 token files from directory
        print(
            f"Trying to login to Garmin Connect using token data from directory '{tokenstore}'...\n"
        )

        # Using Oauth1 and Oauth2 tokens from base64 encoded string
        print(
            f"Trying to login to Garmin Connect using token data from file '{tokenstore_base64}'...\n"
        )
        dir_path = os.path.expanduser(tokenstore_base64)
        with open(dir_path, "r") as token_file:
            tokenstore = token_file.read()

        garmin = Garmin()
        garmin.login(tokenstore)

    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        # Session is expired. You'll need to log in again
        print(
            "Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in '{tokenstore}' for future use.\n"
        )
        try:
            # Ask for credentials if not set as environment variables
            email, password = get_credentials()

            garmin = Garmin(
                email=email, password=password, is_cn=False, prompt_mfa=get_mfa
            )
            garmin.login()
            # Save Oauth1 and Oauth2 token files to directory for next login
            garmin.garth.dump(tokenstore)
            print(
                f"Oauth tokens stored in '{tokenstore}' directory for future use. (first method)\n"
            )
            # Encode Oauth1 and Oauth2 tokens to base64 string and safe to file for next login (alternative way)
            token_base64 = garmin.garth.dumps()
            dir_path = os.path.expanduser(tokenstore_base64)
            with open(dir_path, "w") as token_file:
                token_file.write(token_base64)
            print(
                f"Oauth tokens encoded as base64 string and saved to '{dir_path}' file for future use. (second method)\n"
            )
        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
            requests.exceptions.HTTPError,
        ) as err:
            logger.error(err)
            return None

    return garmin


def parse_datetime(date_str, time_str):
    """Convert date from 'DD.MM.YYYY' to 'YYYY-MM-DD'."""
    iso_timestamp = date_str.strip() + "T" + time_str.strip()
    try:
        return datetime.strptime(iso_timestamp, "%d.%m.%YT%H:%M")
    except ValueError:
        return iso_timestamp


def upload_file(input_filename):
    if not os.path.isfile(input_filename):
        print(f"Input file not found: {input_filename}")
        sys.exit(1)

    with open(input_filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Locate the header that starts with "Date;"
    header_index = None
    first_name = None
    for i, line in enumerate(lines):
        if line.startswith("First name"):
            first_name = line.split("First name")[-1].strip()
        if line.startswith("Date;"):
            header_index = i
            break
    if header_index is None:
        print("CSV header (line starting with 'Date;') not found.")
        sys.exit(1)

    # Init API
    api = init_api(first_name)
    if api is None:
        print(f"Could not log in to Garmin Connect for {first_name}")
        sys.exit(1)

    csv_content = lines[header_index:]
    reader = csv.DictReader(csv_content, delimiter=";")

    readings = []
    for row in reader:
        date_orig = row.get("Date", "").strip()
        time_orig = row.get("Time", "").strip()
        weight = row.get("kg", "").strip()
        bmi = row.get("BMI", "").strip()
        percent_fat = row.get("Body fat", "").strip()
        percent_water = row.get("Water", "").strip()
        muscles = row.get("Muscles", "").strip()
        bone_mass = row.get("Bone", "").strip()

        if date_orig and time_orig and weight and bmi and percent_fat:
            timestamp = parse_datetime(date_orig, time_orig)
            readings.append(
                (
                    timestamp,
                    float(weight),
                    float(bmi),
                    float(percent_fat),
                    float(percent_water),
                    float(muscles) * float(weight) / 100.0,
                    float(bone_mass),
                )
            )

    for (
        timestamp,
        weight,
        bmi,
        percent_fat,
        percent_water,
        muscle_mass,
        bone_mass,
    ) in readings:
        print(
            f"api.add_body_composition({timestamp.isoformat()}, {weight}, {percent_fat}, {percent_water}, {bone_mass}, {muscle_mass}, {bmi})"
        )
        api.add_body_composition(
            timestamp.isoformat(),
            weight=weight,
            percent_fat=percent_fat,
            percent_hydration=percent_water,
            bone_mass=bone_mass,
            muscle_mass=muscle_mass,
            bmi=bmi,
        )

    print(f"Uploading to {first_name}'s Garmin account complete. Processed {len(readings)} readings.")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        input_file = sys.argv[1]
    else:
        exit(1)

    upload_file(input_file)
