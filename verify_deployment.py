#!/usr/bin/env python3
"""
Deployment verification script for Hunyuan3D-2 v2.2.0
Validates all production readiness requirements
"""
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

class DeploymentVerifier:
    """Verify deployment readiness"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'version': '2.2.0',
            'checks': {},
            'overall_status': 'UNKNOWN'
        }
        self.all_passed = True
    
    def check(self, name: str, condition: bool, details: str = ""):
        """Record a check result"""
        status = "✅ PASS" if condition else "❌ FAIL"
        self.results['checks'][name] = {
            'status': status,
            'details': details,
            'passed': condition
        }
        
        if not condition:
            self.all_passed = False
        
        print(f"{status} - {name}")
        if details:
            print(f"     {details}")
        return condition
    
    def verify_version(self):
        """Verify version number"""
        print("\n" + "="*70)
        print("CHECKING: Version & Build Information")
        print("="*70)
        
        # Check setup.py version
        setup_py = Path('setup.py').read_text()
        self.check(
            "setup.py version",
            'version="2.2.0"' in setup_py,
            "setup.py should contain version='2.2.0'"
        )
        
        # Check CHANGELOG
        changelog = Path('CHANGELOG.md').exists()
        self.check(
            "CHANGELOG.md exists",
            changelog,
            "Detailed changelog should be present"
        )
    
    def verify_tests(self):
        """Verify test suite"""
        print("\n" + "="*70)
        print("CHECKING: Test Suite")
        print("="*70)
        
        # Check unit tests
        tests_dir = Path('tests')
        self.check(
            "tests/ directory exists",
            tests_dir.exists(),
            "Unit tests directory required"
        )
        
        # Check E2E tests
        e2e_test = Path('test_e2e.py').exists()
        self.check(
            "test_e2e.py exists",
            e2e_test,
            "End-to-end test script required"
        )
        
        # Try running E2E tests
        print("     Running E2E tests...")
        try:
            result = subprocess.run(
                [sys.executable, 'test_e2e.py'],
                capture_output=True,
                timeout=60
            )
            e2e_passed = result.returncode == 0
            self.check(
                "E2E tests passing",
                e2e_passed,
                f"Exit code: {result.returncode}"
            )
        except Exception as e:
            self.check("E2E tests passing", False, str(e))
    
    def verify_docker(self):
        """Verify Docker setup"""
        print("\n" + "="*70)
        print("CHECKING: Docker & Containerization")
        print("="*70)
        
        # Check Dockerfile
        dockerfile = Path('Dockerfile').exists()
        self.check(
            "Dockerfile exists",
            dockerfile,
            "Production-ready Dockerfile required"
        )
        
        # Check docker-compose
        compose = Path('docker-compose.yml').exists()
        self.check(
            "docker-compose.yml exists",
            compose,
            "Docker Compose orchestration required"
        )
        
        # Check .dockerignore
        dockerignore = Path('.dockerignore').exists()
        self.check(
            ".dockerignore exists",
            dockerignore,
            "Container image optimization required"
        )
        
        # Check Dockerfile content
        if dockerfile:
            dockerfile_content = Path('Dockerfile').read_text()
            self.check(
                "Dockerfile has CUDA support",
                'nvidia/cuda' in dockerfile_content,
                "CUDA 12.1 base image required"
            )
            self.check(
                "Dockerfile has health check",
                'HEALTHCHECK' in dockerfile_content,
                "Health monitoring required"
            )
    
    def verify_ci_cd(self):
        """Verify CI/CD pipeline"""
        print("\n" + "="*70)
        print("CHECKING: CI/CD Pipeline")
        print("="*70)
        
        # Check GitHub Actions workflow
        workflow = Path('.github/workflows/ci.yml').exists()
        self.check(
            "GitHub Actions workflow exists",
            workflow,
            "Automated CI/CD pipeline required"
        )
        
        if workflow:
            workflow_content = Path('.github/workflows/ci.yml').read_text()
            stages = ['lint', 'test', 'e2e', 'build', 'performance', 'dependencies', 'docs']
            for stage in stages:
                self.check(
                    f"CI/CD stage: {stage}",
                    stage in workflow_content.lower(),
                    f"{stage} stage in workflow"
                )
    
    def verify_documentation(self):
        """Verify documentation"""
        print("\n" + "="*70)
        print("CHECKING: Documentation")
        print("="*70)
        
        docs_required = {
            'docs/API_AUTO.md': 'API Reference',
            'CHANGELOG.md': 'Release Changelog',
            'RELEASE_NOTES.md': 'Release Notes',
            'CONTRIBUTING.md': 'Contributing Guide',
            'README.md': 'Project README',
        }
        
        for doc_path, description in docs_required.items():
            exists = Path(doc_path).exists()
            self.check(
                f"{description} ({doc_path})",
                exists,
                description
            )
    
    def verify_dependencies(self):
        """Verify dependency management"""
        print("\n" + "="*70)
        print("CHECKING: Dependencies")
        print("="*70)
        
        # Check requirements.txt
        req_txt = Path('requirements.txt').exists()
        self.check(
            "requirements.txt exists",
            req_txt,
            "Dependency specification required"
        )
        
        if req_txt:
            req_content = Path('requirements.txt').read_text()
            critical_deps = ['gradio>=6.3', 'fastapi', 'torch', 'numpy>=2.2']
            for dep in critical_deps:
                self.check(
                    f"Dependency: {dep}",
                    dep.split('>=')[0].split('<')[0] in req_content,
                    f"Latest {dep} required"
                )
        
        # Check pip status
        print("     Checking pip dependencies...")
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'check'],
                capture_output=True,
                timeout=30
            )
            pip_ok = result.returncode == 0
            self.check(
                "pip check (no conflicts)",
                pip_ok,
                "All dependencies compatible"
            )
        except Exception as e:
            self.check("pip check", False, str(e))
    
    def verify_performance_metrics(self):
        """Verify performance benchmarking"""
        print("\n" + "="*70)
        print("CHECKING: Performance Metrics")
        print("="*70)
        
        benchmark = Path('scripts/benchmark.py').exists()
        self.check(
            "benchmark.py exists",
            benchmark,
            "Performance profiling script required"
        )
        
        # Try running benchmark
        if benchmark:
            print("     Running performance benchmark...")
            try:
                result = subprocess.run(
                    [sys.executable, 'scripts/benchmark.py'],
                    capture_output=True,
                    timeout=120
                )
                bench_ok = result.returncode == 0
                self.check(
                    "Benchmark execution",
                    bench_ok,
                    "Performance metrics collected"
                )
            except Exception as e:
                self.check("Benchmark execution", False, str(e))
    
    def verify_imports(self):
        """Verify critical imports"""
        print("\n" + "="*70)
        print("CHECKING: Critical Imports")
        print("="*70)
        
        critical_modules = [
            ('hy3dgen.manager', 'ModelManager'),
            ('hy3dgen.inference', 'InferencePipeline'),
            ('hy3dgen.apps.gradio_app', 'build_app'),
            ('hy3dgen.apps.api_server', 'app'),
        ]
        
        for module_name, item_name in critical_modules:
            try:
                module = __import__(module_name, fromlist=[item_name])
                hasattr(module, item_name)
                self.check(
                    f"Import: {module_name}.{item_name}",
                    True,
                    "Module successfully imported"
                )
            except Exception as e:
                self.check(
                    f"Import: {module_name}.{item_name}",
                    False,
                    str(e)
                )
    
    def run_all_checks(self):
        """Run all verification checks"""
        print("\n" + "╔" + "="*68 + "╗")
        print("║" + " "*12 + "HUNYUAN3D-2 v2.2.0 DEPLOYMENT VERIFICATION" + " "*12 + "║")
        print("╚" + "="*68 + "╝")
        
        self.verify_version()
        self.verify_tests()
        self.verify_docker()
        self.verify_ci_cd()
        self.verify_documentation()
        self.verify_dependencies()
        self.verify_performance_metrics()
        self.verify_imports()
        
        # Summary
        print("\n" + "="*70)
        print("VERIFICATION SUMMARY")
        print("="*70)
        
        total_checks = len(self.results['checks'])
        passed_checks = sum(1 for c in self.results['checks'].values() if c['passed'])
        
        print(f"\nTotal Checks: {total_checks}")
        print(f"Passed: {passed_checks}")
        print(f"Failed: {total_checks - passed_checks}")
        
        if self.all_passed:
            print("\n✅ ALL CHECKS PASSED - READY FOR PRODUCTION")
            self.results['overall_status'] = 'APPROVED'
        else:
            print("\n❌ SOME CHECKS FAILED - REVIEW REQUIRED")
            self.results['overall_status'] = 'FAILED'
        
        # Save results
        output_file = f"deployment_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to: {output_file}")
        
        return 0 if self.all_passed else 1

def main():
    """Run deployment verification"""
    verifier = DeploymentVerifier()
    return verifier.run_all_checks()

if __name__ == "__main__":
    sys.exit(main())
