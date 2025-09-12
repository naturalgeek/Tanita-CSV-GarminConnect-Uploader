# tanita2garminconnect

Python script to automate converting and uploading CSV files from Tanita to Garmin Connect.

## Supported Scales
Not sure, my one is a tanita BC-601,603 and 613 are supported. Possibly more.

if your scales CSV matches the following format, its probably gonna work:
{0,16,~0,2,~1,2,~2,3,~3,4,MO,"BC-601",DT,"12/09/2025",Ti,"09:15:13",Bt,0,GE,1,AG,40,Hm,172.0,AL,2,Wk,67.0,MI,22.6,FW,20.7,Fr,15.8,Fl,16.4,FR,17.0,FL,18.2,FT,23.5,mW,50.4,mr,2.9,ml,2.9,mR,8.8,mL,8.5,mT,27.3,bW,2.7,IF,7,rD,2748,rA,38,ww,56.4,CS,CA


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

In case you want to delete data for each day prior to adding the data from the CSV file, comment out line 201-204.

## Credits
Forked from https://github.com/pedropombeiro/beurer2garminconnect and altered to only support uploading CSV's from tanita scales.

