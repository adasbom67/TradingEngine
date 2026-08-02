from app.operations.deployment import DeploymentVerifier

if __name__ == "__main__":
    result = DeploymentVerifier().verify(".")
    print(f"Compilation: {'PASS' if result.compilation_ok else 'FAIL'}")
    print(f"Tests: {'PASS' if result.tests_ok else 'FAIL'}")
    print(result.test_output)
    raise SystemExit(0 if result.successful else 1)
