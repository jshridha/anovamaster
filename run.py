from AnovaMaster import AnovaConfiguration, AnovaMaster

if __name__ == '__main__':
    print("Importing config")
    config = AnovaConfiguration()
    print("Setting up connection")
    my_anova = AnovaMaster(config)
    import time
    while True:
        time.sleep(5)
        print("Attempting to fetch status")
        my_anova.fetch_status()
        my_anova.dump_status()
