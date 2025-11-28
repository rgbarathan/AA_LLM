#!/usr/bin/env python
"""
Test runner script - execute all test suites.
"""
import sys
import os
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests_with_pytest():
    """Run tests using pytest if available."""
    try:
        import pytest
        print("🧪 Running tests with pytest...\n")
        result = pytest.main([
            "tests/",
            "-v",
            "--tb=short",
            "--color=yes"
        ])
        return result == 0
    except ImportError:
        return None


def run_tests_direct():
    """Run tests directly without pytest."""
    print("🧪 Running test modules directly...\n")
    
    test_modules = [
        "tests.test_knowledge_base",
        "tests.test_retrieval",
        "tests.test_integration",
        "tests.test_performance",
    ]
    
    results = {}
    for module in test_modules:
        print(f"\n{'='*60}")
        print(f"Running {module}...")
        print(f"{'='*60}")
        
        try:
            __import__(module)
            module_obj = sys.modules[module]
            
            # Find and run main function
            if hasattr(module_obj, 'run_all_integration_tests'):
                success = module_obj.run_all_integration_tests()
            elif hasattr(module_obj, 'run_performance_benchmarks'):
                success = module_obj.run_performance_benchmarks()
            else:
                # Run test functions
                test_functions = [
                    getattr(module_obj, name)
                    for name in dir(module_obj)
                    if name.startswith('test_') and callable(getattr(module_obj, name))
                ]
                
                for test_func in test_functions:
                    try:
                        test_func()
                    except Exception as e:
                        print(f"✗ {test_func.__name__} failed: {e}")
                        success = False
                        break
                else:
                    success = True
            
            results[module] = success
        except Exception as e:
            print(f"✗ Error running {module}: {e}")
            import traceback
            traceback.print_exc()
            results[module] = False
    
    return results


def main():
    print("\n" + "🚀 "*20)
    print("TELECOM ADVISOR - TEST SUITE")
    print("🚀 "*20 + "\n")
    
    # Try pytest first
    pytest_result = run_tests_with_pytest()
    
    if pytest_result is not None:
        if pytest_result:
            print("\n✅ All tests passed with pytest!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
    
    # Fallback to direct execution
    print("⚠️  pytest not installed, running tests directly...\n")
    results = run_tests_direct()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for module, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {module}")
    
    print(f"\n{passed}/{total} test modules passed")
    
    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
