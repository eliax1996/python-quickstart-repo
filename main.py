import asyncio
import logging

from python_quickstart_repo.config.config import WorkingMode
from python_quickstart_repo.config.program_launcher import load_config, consumer_program, producer_program

if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    config = load_config()

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        level=logging.DEBUG if config.general_config.debug else logging.INFO,
    )

    if config.general_config.working_mode == WorkingMode.PRODUCER:
        program = producer_program(config.producer_config)
    else:
        program = consumer_program(config.consumer_config)

    asyncio.run(program)
