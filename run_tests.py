"""
Test Runner for Bitcoin Model V2
Provides convenient commands to run different test categories.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py unit               # Run unit tests only
    python run_tests.py integration        # Run integration tests only
    python run_tests.py performance        # Run performance benchmarks
    python run_tests.py quick              # Run unit tests (fastest)
    python run_tests.py full               # Run all tests including slow
    python run_tests.py coverage           # Run with coverage report
"""

import sys
import subprocess
from pathlib import Path


class TestRunner:
    """Unified test runner for all test categories."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent / 'tests'
        self.base_cmd = [sys.executable, '-m', 'pytest']
    
    def run_all_tests(self):
        """Run all tests."""
        print("\n" + "="*80)
        print("RUNNING ALL TESTS")
        print("="*80 + "\n")
        cmd = self.base_cmd + [str(self.test_dir), '-v']
        return subprocess.run(cmd).returncode
    
    def run_unit_tests(self):
        """Run unit tests only (fast)."""
        print("\n" + "="*80)
        print("RUNNING UNIT TESTS")
        print("="*80 + "\n")
        cmd = self.base_cmd + [str(self.test_dir), '-v', '-m', 'unit']
        return subprocess.run(cmd).returncode
    
    def run_integration_tests(self):
        """Run integration tests."""
        print("\n" + "="*80)
        print("RUNNING INTEGRATION TESTS")
        print("="*80 + "\n")
        cmd = self.base_cmd + [str(self.test_dir), '-v', '-m', 'integration']
        return subprocess.run(cmd).returncode
    
    def run_performance_tests(self):
        """Run performance benchmarks."""
        print("\n" + "="*80)
        print("RUNNING PERFORMANCE BENCHMARKS")
        print("="*80 + "\n")
        cmd = self.base_cmd + [str(self.test_dir), '-v', '-m', 'performance']
        return subprocess.run(cmd).returncode
    
    def run_quick_tests(self):
        """Run quick tests (unit only, no slow tests)."""
        print("\n" + "="*80)
        print("RUNNING QUICK TESTS (UNIT)")
        print("="*80 + "\n")
        cmd = self.base_cmd + [str(self.test_dir), '-v', '-m', 'unit', '-m', 'not slow']
        return subprocess.run(cmd).returncode
    
    def run_full_suite(self):
        """Run complete test suite including slow tests."""
        print("\n" + "="*80)
        print("RUNNING FULL TEST SUITE")
        print("="*80 + "\n")
        cmd = self.base_cmd + [str(self.test_dir), '-v']
        return subprocess.run(cmd).returncode
    
    def run_with_coverage(self):
        """Run tests with coverage report."""
        print("\n" + "="*80)
        print("RUNNING TESTS WITH COVERAGE")
        print("="*80 + "\n")
        cmd = self.base_cmd + [
            str(self.test_dir), 
            '-v',
            '--cov=Code',
            '--cov-report=html',
            '--cov-report=term-missing'
        ]
        result = subprocess.run(cmd).returncode
        
        if result == 0:
            print("\n✓ Coverage report generated: htmlcov/index.html")
        
        return result
    
    def run_specific_module(self, module_name):
        """Run tests for specific module."""
        test_file = self.test_dir / f'test_{module_name}.py'
        
        if not test_file.exists():
            print(f"\n✗ Test file not found: {test_file}")
            print(f"\nAvailable test modules:")
            for f in self.test_dir.glob('test_*.py'):
                print(f"  - {f.stem}")
            return 1
        
        print("\n" + "="*80)
        print(f"RUNNING TESTS FOR {module_name.upper()}")
        print("="*80 + "\n")
        cmd = self.base_cmd + [str(test_file), '-v']
        return subprocess.run(cmd).returncode
    
    def print_help(self):
        """Print help message."""
        help_text = """
Bitcoin Model V2 Test Runner

Usage:
    python run_tests.py [command]

Commands:
    (none)              Run all tests
    unit                Run unit tests only (fast)
    integration         Run integration tests
    performance         Run performance benchmarks
    quick               Run quick tests (unit, no slow)
    full                Run complete test suite
    coverage            Run with coverage report
    data                Run data preparation tests
    model               Run model training tests
    prediction          Run prediction service tests
    error               Run error handling tests
    help                Show this help message

Examples:
    python run_tests.py
    python run_tests.py unit
    python run_tests.py integration
    python run_tests.py coverage
    python run_tests.py model

Test Categories:
    @pytest.mark.unit           - Unit tests (fast, <1s each)
    @pytest.mark.integration    - Integration tests (medium)
    @pytest.mark.performance    - Performance benchmarks (can be slow)
    @pytest.mark.database       - Database-dependent tests
    @pytest.mark.slow           - Slow-running tests (>1s)

Configuration:
    pytest.ini                  - Test configuration file
    tests/conftest.py          - Pytest fixtures and configuration
        """
        print(help_text)
    
    def main(self, args=None):
        """Main entry point."""
        if args is None:
            args = sys.argv[1:]
        
        if not args:
            return self.run_all_tests()
        
        command = args[0].lower()
        
        command_map = {
            'unit': self.run_unit_tests,
            'integration': self.run_integration_tests,
            'performance': self.run_performance_tests,
            'quick': self.run_quick_tests,
            'full': self.run_full_suite,
            'coverage': self.run_with_coverage,
            'help': self.print_help,
        }
        
        # Check for module-specific tests
        if command.startswith('test_'):
            module_name = command.replace('test_', '').replace('.py', '')
        else:
            module_name = command
        
        # Check if it's a module test
        test_file = self.test_dir / f'test_{module_name}.py'
        if test_file.exists() and command not in command_map:
            return self.run_specific_module(module_name)
        
        if command in command_map:
            return command_map[command]()
        else:
            print(f"\n✗ Unknown command: {command}")
            print(f"\nValid commands: {', '.join(command_map.keys())}")
            print(f"\nRun 'python run_tests.py help' for more information")
            return 1


if __name__ == '__main__':
    runner = TestRunner()
    exit_code = runner.main()
    sys.exit(exit_code)
