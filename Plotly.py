from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr

# Inicialize uma sessão Spark
spark = SparkSession.builder.appName("Exemplo").getOrCreate()

# Carregue os dados da sua fonte de dados (substitua 'source_path' pelo caminho do seu arquivo)
df = spark.read.option("multiline", "true").json("source_path")

# Selecione as colunas desejadas
result = df.select(
    "fullvisitorid",
    "visitstarttime",
    "clientid",
    "userid",
    "visitnumber",
    "visitid",
    "date",
    col("totals.newVisits").alias("newvisits"),
    col("trafficSource.adContent").alias("adcontent"),
    col("trafficSource.campaign").alias("campaign"),
    col("trafficSource.campaignCode").alias("campaigncode"),
    expr("UPPER(CAST(trafficSource.isTrueDirect AS STRING)) AS istruedirect"),
    "trafficSource.keyword",
    "trafficSource.medium",
    "trafficSource.referralPath",
    "trafficSource.source",
    "socialEngagementType",
    "channelGrouping",
    "device.browser",
    "device.browserSize",
    "device.browserVersion",
    "device.mobileDeviceInfo",
    "device.operatingSystem",
    "device.operatingSystemVersion",
    "device.mobileDeviceBranding",
    "device.screenColors",
    "geoNetwork.networkLocation",
    "geoNetwork.networkDomain",
    "geoNetwork.city",
    "geoNetwork.country",
    "geoNetwork.region",
    "geoNetwork.cityId",
    "geoNetwork.latitude",
    "geoNetwork.longitude",
    "h.hitNumber",
    expr("UPPER(CAST(h.isEntrance AS STRING)) AS isentrance"),
    expr("UPPER(CAST(h.isExit AS STRING)) AS isexit"),
    expr("UPPER(CAST(h.isInteraction AS STRING)) AS isinteraction"),
    "h.hour",
    "h.minute",
    "h.time",
    "h.referer",
    col("h.transaction.transactionId").alias("transactionid"),
    col("h.transaction.transactionCoupon").alias("transactioncoupon"),
    col("h.transaction.transactionRevenue").alias("transactionrevenue"),
    col("h.transaction.transactionTax").alias("transactiontax"),
    col("h.transaction.transactionShipping").alias("transactionshipping"),
    col("h.transaction.affiliation").alias("affiliation"),
    col("h.transaction.currencyCode").alias("currencycode"),
    col("h.transaction.localTransactionRevenue").alias("localtransactionrevenue"),
    col("h.transaction.localTransactionTax").alias("localtransactiontax"),
    col("h.transaction.localTransactionShipping").alias("localtransactionshipping"),
    col("h.refund.localRefundAmount").alias("localrefundamount"),
    col("h.refund.refundAmount").alias("refundamount"),
    "h.type",
    col("h.page.pagePath").alias("pagepath"),
    col("h.page.hostname").alias("hostname"),
    col("h.page.pageTitle").alias("pagetitle"),
    col("h.page.searchKeyword").alias("searchkeyword"),
    col("h.page.searchCategory").alias("searchcategory"),
    col("h.contentInfo.contentDescription").alias("contentdescription"),
    col("h.eventInfo.eventCategory").alias("eventcategory"),
    col("h.eventInfo.eventAction").alias("eventaction"),
    col("h.eventInfo.eventLabel").alias("eventlabel"),
    col("h.eventInfo.eventValue").alias("eventvalue"),
    col("h.appInfo.appInstallerId").alias("appinstallerid"),
    col("h.appInfo.appName").alias("appname"),
    col("h.appInfo.appVersion").alias("appversion"),
    col("h.appInfo.appId").alias("appid"),
    col("h.appInfo.screenName").alias("screenname"),
    col("h.appInfo.landingScreenName").alias("landingscreenname"),
    col("h.appInfo.exitScreenName").alias("exitscreenname"),
    col("h.appInfo.screenDepth").alias("screendepth"),
    expr(
        "CONCAT(CAST(year AS STRING), CAST(month AS STRING), CAST(day AS STRING)) AS anomesdia"
    ),
    "h.promotion",
    "h.customdimensions",
)

# Exiba o DataFrame resultante
result.show()

# Para salvar o resultado em um novo arquivo JSON (substitua 'output_path' pelo caminho desejado)
result.write.json("output_path")