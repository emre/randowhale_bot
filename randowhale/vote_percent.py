
import random
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()


# default probability dimensions
PROBABILITY_DIMENSIONS = (
    (1, 25, 0.4),
    (25, 50, 0.3),
    (50, 75, 0.2),
    (75, 99, 0.09),
    (99, 100, 0.01),
)


class VotePercent:
    """
    A vote percent generator based on the probability index.
    """

    def __init__(self, probability_dimensions=None):
        self.probability_dimensions = probability_dimensions or \
                                      PROBABILITY_DIMENSIONS
        self.check_validity_of_dimensions()
        self.choices = []
        self.weights = []

    def check_validity_of_dimensions(self):
        weight = sum([p[2] * 100 for p in self.probability_dimensions])
        if weight != 100:
            raise ValueError("Invalid probability dimensions. Sum of the "
                             "weights must be 1. It's %s", weight)

    def get_population_and_weight(self):
        choices = []
        weights = []
        for start, end, probability in self.probability_dimensions:
            population = []
            for i in range(start, end):
                population.append(i)
            choices.append(population)
            weights.append(probability)

        return choices, weights

    def pick_percent(self):
        population, weight = self.get_population_and_weight()
        dimensioned_choices = random.choices(
            population=population, weights=weight, k=1)
        return random.choice(dimensioned_choices[0])
