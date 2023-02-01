import asyncio
import logging

from python_quickstart_repo.config.config import WorkingMode
from python_quickstart_repo.config.program_launcher import (
    consumer_program,
    load_config,
    producer_program,
)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    config = load_config()

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        level=logging.DEBUG if config.general_config.debug else logging.INFO,
    )

    if config.general_config.working_mode == WorkingMode.PRODUCER:
        if config.producer_config is None:
            raise ValueError("Producer config is not present in the config file, couldn't start the program")
        program = producer_program(config.producer_config)
    else:
        if config.consumer_config is None:
            raise ValueError("Consumer config is not present in the config file, couldn't start the program")
        program = consumer_program(config.consumer_config)

    asyncio.run(program)
