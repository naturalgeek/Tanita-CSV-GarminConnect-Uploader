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


def init_api(user):
    """Initialize Garmin API with your credentials."""

    tokenstore = os.getenv("GARMINTOKENS") or f"~/.garminconnect.{user}"
    tokenstore_base64 = (
        os.getenv("GARMINTOKENS_BASE64") or f"~/.garminconnect_base64.{user}"
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
        return datetime.strptime(iso_timestamp, "%d/%m/%YT%H:%M:%S")
    except ValueError:
        return iso_timestamp


def upload_file(input_filename):
    if not os.path.isfile(input_filename):
        print(f"Input file not found: {input_filename}")
        sys.exit(1)

    with open(input_filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header_index = None
    user = "default"

    # Init API
    api = init_api(user)
    if api is None:
        print(f"Could not log in to Garmin Connect for {user}")
        sys.exit(1)

    csv_content = lines[header_index:]
    reader = csv.reader(csv_content, delimiter=",")

    readings = []
    for row in reader:
        for index, identifier in enumerate(row):
            if identifier == "Wk": weight_addr = index+1
            if identifier == "MI": bmi_addr = index+1
            if identifier == "DT": date_addr = index+1
            if identifier == "Ti": time_addr = index+1
            if identifier == "FW": percent_fat_addr = index+1
            if identifier == "ww": percent_hydration_addr = index+1
            if identifier == "mW": muscle_mass_addr = index+1
            if identifier == "IF": visceral_fat_rating_addr = index+1
            if identifier == "bW": bone_mass_addr = index+1
            if identifier == "AL": physique_rating_addr = index+1
            if identifier == "rA": metabolic_age_addr = index+1
            if identifier == "rD": caloric_intake_addr = index+1
        break

    for row in reader:
        date_orig = row[date_addr]
        time_orig = row[time_addr]
        weight = row[weight_addr]
        bmi = row[bmi_addr]
        percent_fat = row[percent_fat_addr]
        percent_water = row[percent_hydration_addr]
        muscles = row[muscle_mass_addr]
        bone_mass = row[bone_mass_addr]
        physique_rating = row[physique_rating_addr]
        metabolic_age = row[metabolic_age_addr]
        caloric_intake = row[caloric_intake_addr]
        visceral_fat_rating = row[visceral_fat_rating_addr]

        if date_orig and time_orig and weight and bmi and percent_fat and visceral_fat_rating and caloric_intake and metabolic_age and physique_rating:
            timestamp = parse_datetime(date_orig, time_orig)
            readings.append(
                (
                    timestamp,
                    float(weight),
                    float(bmi),
                    float(percent_fat),
                    float(percent_water),
                    float(muscles),
                    float(bone_mass),
                    float(physique_rating),
                    float(metabolic_age),
                    float(caloric_intake),
                    float(visceral_fat_rating),
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
        physique_rating,
        metabolic_age,
        caloric_intake,
        visceral_fat_rating,
    ) in readings:

#        Comment out if you want to delete all content from the newly added dates (replacing manual weigh-ins with this extensive automated ones.

#        api.delete_weigh_ins(
#            timestamp.strftime("%Y-%m-%d"),
#            delete_all=True,
#		)
#        print("Weigh-ins deleted successfully!") 
        api.add_body_composition(
            timestamp.isoformat(),
            weight=weight,
            percent_fat=percent_fat,
            percent_hydration=percent_water,
            bone_mass=bone_mass,
            muscle_mass=muscle_mass,
            physique_rating=physique_rating,
            metabolic_age=metabolic_age,
            visceral_fat_rating=visceral_fat_rating,
            bmi=bmi,
        )
        print(
            f"api.add_body_composition({timestamp.isoformat()}, {weight}, {percent_fat}, {percent_water}, {bone_mass}, {muscle_mass}, {physique_rating}, {metabolic_age}, {caloric_intake}, {visceral_fat_rating}, {bmi})"
        )

    print(f"Uploading to {user}'s Garmin account complete. Processed {len(readings)} readings.")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        input_file = sys.argv[1]
    else:
        exit(1)

    upload_file(input_file)
