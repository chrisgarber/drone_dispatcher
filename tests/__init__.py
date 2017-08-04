from droneDelivery import *
import unittest

class LocationTest(unittest.TestCase):

   def test_getDistance(self):
      self.assertAlmostEqual(location(20,20).getDistance(location(-20,-20)), 6224.8900801594446, 9)
      


if __name__ == '__main__':
    unittest.main()