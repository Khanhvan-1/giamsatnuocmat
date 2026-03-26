from django.http import JsonResponse
from django.shortcuts import render
import psycopg2
import json


def get_points(request):

    conn = psycopg2.connect(

    dbname="webgis_nuoc",
    user="postgres",
    password="123456",
    host="localhost",
    port="5432"

    )

    cur=conn.cursor()

    cur.execute("""

    SELECT
    ma_diem,
    ph,
    "do",
    bod5,
    cod,
    nh4,
    caliform,
    ST_AsGeoJSON(geom)

    FROM diem_quan_trac_clean

    """)

    rows=cur.fetchall()

    data=[]

    for r in rows:

        data.append({

        "ma_diem":r[0],
        "ph":r[1],
        "do":r[2],
        "bod5":r[3],
        "cod":r[4],
        "nh4":r[5],
        "caliform":r[6],
        "geometry":json.loads(r[7])

        })

    return JsonResponse(data,safe=False)

def map_view(request):
    return render(request, 'map.html')

def dashboard(request):
    return render(request,'dashboard.html')