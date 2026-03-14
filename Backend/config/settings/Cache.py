from config.env import env

REDIS_HOSTNAME = env("REDIS_HOSTNAME")

CACHEOPS_REDIS = {
    "host": REDIS_HOSTNAME,  # Redis server host
    "port": 6379,  # Redis server port
    "db": 1,  # Redis database number
}

CACHEOPS = {
    # Cache all transactions for 1 hour
    "transactions.transactionslog": {
        "ops": {"get", "fetch"},
        "timeout": 60 * 60,
    },
    # Cache the filtered queries
    "*.*": {
        "timeout": 60 * 15,  # 15 minutes default
    },
}
