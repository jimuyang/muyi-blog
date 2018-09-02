import config_dev

configs = config_dev.configs

try:
    import config_prod
    # configs = merge(configs, config_prod.configs)
except ImportError:
    pass