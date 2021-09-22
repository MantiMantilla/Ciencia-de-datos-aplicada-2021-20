import os
from pyspark.sql import SparkSession
os.environ['PYSPARK_PYTHON'] = "./environment/bin/python"
spark = SparkSession.builder.config(
    "spark.archives",  # 'spark.yarn.dist.archives' in YARN.
    "pyspark_venv.tar.gz#environment").appName("Ciencia de datos").getOrCreate()
import datetime
from shapely.geometry import Point, Polygon, shape
from shapely import wkb, wkt
from pyspark.sql.functions import *
from pyspark.sql.types import StringType, IntegerType, FloatType, DoubleType,DecimalType,LongType
from functools import reduce
from pyspark.sql import DataFrame
import shapely.speedups
shapely.speedups.enable() # this makes some spatial queries run faster
currentdate = datetime.datetime.now().strftime("%Y-%m-%d_%I-%M") #Guarda fecha para salidas

#importar de datos por archivo de mes segun su estructura de datos, titulos y columnas con el mismo tipo de datos:
taxis_2017 = spark.read.csv("/datos/taxis/individual/yellow_tripdata_2017-*.csv.gz", header=True).cache()
taxis_2017 = taxis_2017.select(year(col("tpep_pickup_datetime")).alias("year"),month(col("tpep_pickup_datetime")).alias("month"),dayofweek(col("tpep_pickup_datetime")).alias("dayofweek"),dayofmonth(col("tpep_pickup_datetime")).alias("dayofmonth"), hour(col("tpep_pickup_datetime")).alias("hour"), round((to_timestamp(col("tpep_dropoff_datetime")).cast("long") - to_timestamp(col("tpep_pickup_datetime")).cast("long"))/60).alias("total_time_min"), col("trip_distance"), col("PULocationID"), col("DOLocationID"), col("payment_type"), col("fare_amount"), col("tip_amount"), col("tolls_amount") , col("total_amount"))
taxis_2018 = spark.read.csv("/datos/taxis/individual/yellow_tripdata_2018-*.csv.gz", header=True).cache()
taxis_2018 = taxis_2018.select(year(col("tpep_pickup_datetime")).alias("year"),month(col("tpep_pickup_datetime")).alias("month"),dayofweek(col("tpep_pickup_datetime")).alias("dayofweek"),dayofmonth(col("tpep_pickup_datetime")).alias("dayofmonth"), hour(col("tpep_pickup_datetime")).alias("hour"), round((to_timestamp(col("tpep_dropoff_datetime")).cast("long") - to_timestamp(col("tpep_pickup_datetime")).cast("long"))/60).alias("total_time_min"), col("trip_distance"), col("PULocationID"), col("DOLocationID"), col("payment_type"), col("fare_amount"), col("tip_amount"), col("tolls_amount") , col("total_amount"))
taxis_2019 = spark.read.csv("/datos/taxis/individual/yellow_tripdata_2019-*.csv.gz", header=True).cache()
taxis_2019 = taxis_2019.select(year(col("tpep_pickup_datetime")).alias("year"),month(col("tpep_pickup_datetime")).alias("month"),dayofweek(col("tpep_pickup_datetime")).alias("dayofweek"),dayofmonth(col("tpep_pickup_datetime")).alias("dayofmonth"), hour(col("tpep_pickup_datetime")).alias("hour"), round((to_timestamp(col("tpep_dropoff_datetime")).cast("long") - to_timestamp(col("tpep_pickup_datetime")).cast("long"))/60).alias("total_time_min"), col("trip_distance"), col("PULocationID"), col("DOLocationID"), col("payment_type"), col("fare_amount"), col("tip_amount"), col("tolls_amount") , col("total_amount"))

#Union de todos los anios a un unico dataset
dfss = [taxis_2017,taxis_2018,taxis_2019]
allyears = reduce(DataFrame.union, dfss)

#Filtro por anios fuera del rango analizado ya que representa ruido
validateYears=["2017","2018","2019"]
allyears = allyears.filter(allyears.year.isin(validateYears))

#Convertir tipo de pago
allyears = allyears.replace(['1','2','3','4','5'],['CREDIT','CASH','NOCHARGE','DISPUTE','UNKNOWN'],'payment_type').select("*")

#Convertir zonas
zones = spark.read.csv("grupo05/entradazonas/zone_lookup.csv", header=True)
allyears = allyears.join(zones, allyears.PULocationID == zones.LocationID, 'left').select(allyears["*"], (zones.Zone).alias('PULocation') )
allyears = allyears.join(zones, allyears.DOLocationID == zones.LocationID, 'left').select(allyears["*"], (zones.Zone).alias('DOLocation') )

#Convertir los datos por tipo de columna
allyears = allyears.withColumn("trip_distance",allyears["trip_distance"].cast('float'))
allyears = allyears.withColumn("total_amount",allyears["total_amount"].cast('float'))
allyears = allyears.withColumn("fare_amount",allyears["fare_amount"].cast('float'))
allyears = allyears.withColumn("tip_amount",allyears["tip_amount"].cast('float'))
allyears = allyears.withColumn("tolls_amount",allyears["tolls_amount"].cast('float'))

#allyearsgrouped=allyears.groupBy("PULocation", "DOLocation", "year").count()

#Arreglar y exportar la salida final
allyearsgrouped.write.parquet('./grupo05/salidas/puntogRespuesta_'+currentdate)

#Exportar respuestas parquet a csv para mejor lectura
parDFG=spark.read.parquet("./grupo05/salidas/puntogRespuesta_"+currentdate)
parDFG.write.csv('./grupo05/salidas/puntogRespuestaCSV_'+currentdate)