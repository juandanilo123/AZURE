El proyecto implementa un pipeline moderno de ingeniería de datos para el escenario RetailMax. La solución utiliza una arquitectura Medallion con capas Bronze, Silver y Gold. Hasta el momento se completó la preparación local en Python, la generación y carga de datos sintéticos en Azure SQL Database, la creación de la infraestructura principal en Azure, la ingesta de las siete tablas hacia Bronze mediante Azure Data Factory y el desarrollo del procesamiento Silver en Azure Databricks con PySpark y Delta Lake

Datos                   	Valor
Escenario            	Retail y Comercio Electrónico
Plataforma          	Microsoft Azure
Grupo de recursos	    RETAIL_COMERCIO_ELECTRONICO
Base de datos	        Databasecomercio
Cuenta ADLS Gen2	    Mantenimientos
