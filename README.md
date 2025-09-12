# tanita2garminconnect

Python script to automate converting and uploading CSV files from Tanita to Garmin Connect.

## Requirements

- Python 3
- [just](https://github.com/casey/just)

## Setting up

To create the Python virtual environment, run the following command:

```shell
just setup
```

## Uploading to Garmin Connect


```shell
./upload_tanita_csv_to_garmin.py <path/to/file.csv>
```

The script will ask you to log in to Garmin Connect if needed. The login will be saved to a dedicated file named after
the user's first name.
