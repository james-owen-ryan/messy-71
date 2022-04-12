import config
from messy import MESSY


if __name__ == "__main__":
    if config.OUTPUT_TO_FILE:
        print(f"Writing output to '{config.LOG_FILE}'...")
        log_file = open(config.LOG_FILE, 'w')
        log_file.close()
        with open(config.LOG_FILE, 'a') as log_file:
            messy = MESSY()
            for _ in range(config.NUMBER_OF_TIME_FRAMES):
                messy.simulate()
            messy.terminate()
    else:
        messy = MESSY()
        print(f"\nSimulating universe #{config.RANDOM_SEED}...\n")
        for _ in range(config.NUMBER_OF_TIME_FRAMES):
            messy.simulate()
        messy.terminate()
        messy.report()
