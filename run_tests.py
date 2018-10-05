import os
import sys
# Standard imports
import unittest
import xmlrunner
import argparse

DEFAULT_DIRECTORY = os.path.join('.', 'test-reports')


if __name__ == '__main__':
    # get output directory from command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output_dir', nargs=1, type=str, default=[DEFAULT_DIRECTORY],
                        help='The directory to save the test reports')
    args = parser.parse_args()
    xml_dir = args.output_dir[0]

    # Load tests from test suites
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "tests"))
    test_suite = unittest.TestLoader().discover(test_dir, pattern="test_*.py")

    print("\n\n------ BEGINNING Experiment Database Populator UNIT TESTS ------")
    ret_vals = list()
    ret_vals.append(xmlrunner.XMLTestRunner(output=xml_dir).run(test_suite))
    print("------ UNIT TESTS COMPLETE ------\n\n")

    # Return failure exit code if a test failed
    sys.exit(False in ret_vals)
