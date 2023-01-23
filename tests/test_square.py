import unittest

from python_quickstart_repo.square import Square
from python_quickstart_repo.shape import Shape


class TestSquare(unittest.TestCase):
    def test_create_square_negative_length(self):
        with self.assertRaises(ValueError):
            Square(-1)

    def test_square_instance_of_shape(self):
        square = Square(10)
        self.assertIsInstance(square, Shape)

    def test_area(self):
        square = Square(10)
        area = square.area()
        self.assertEqual(area, 100)
