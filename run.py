from AnovaMaster import AnovaConfiguration, AnovaMaster

if __name__ == '__main__':
    print("Importing config")
    config = AnovaConfiguration()
    print("Setting up connection")
    my_anova = AnovaMaster(config)
    print("Running run loop")
    my_anova.run()
