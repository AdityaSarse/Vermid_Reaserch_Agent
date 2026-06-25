import unittest
import sys

if __name__ == "__main__":
    print("Running VeriMed Research Agent Unit Tests...")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="tests")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if not result.wasSuccessful():
        sys.exit(1)
    sys.exit(0)
