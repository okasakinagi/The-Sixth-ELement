try:
    import pymysql

    pymysql.version_info = (2, 2, 7, "final", 0)
    pymysql.__version__ = "2.2.7"
    pymysql.install_as_MySQLdb()
except Exception:
    pass
