#!/usr/bin/env python3
"""
Convert a JUnit XML report (as produced by `pytest --junitxml=...`) into
test-results.json, matching schemas/test_results.schema.json.

Usage:
    python3 scripts/junit_to_json.py <junit_xml_file> <output_json_file>
"""
import json
import sys
import xml.etree.ElementTree as ET


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: junit_to_json.py <junit_xml_file> <output_json_file>")
        sys.exit(2)

    xml_path, out_path = sys.argv[1], sys.argv[2]

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # JUnit XML from pytest can be a single <testsuite> or a <testsuites>
    # wrapper containing one or more <testsuite> elements.
    suites = root.findall("testsuite") if root.tag == "testsuites" else [root]

    total = passed = failed = 0
    failures = []

    for suite in suites:
        for case in suite.findall("testcase"):
            total += 1
            failure = case.find("failure")
            error = case.find("error")
            if failure is not None or error is not None:
                failed += 1
                node = failure if failure is not None else error
                test_name = f'{case.get("classname", "")}::{case.get("name", "")}'
                message = (node.get("message") or "").strip() or "no message provided"
                failures.append({"test_name": test_name, "message": message})
            else:
                passed += 1

    result = {
        "status": "pass" if failed == 0 else "fail",
        "total": total,
        "passed": passed,
        "failed": failed,
        "failures": failures,
    }

    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"wrote {out_path}: {passed}/{total} passed")


if __name__ == "__main__":
    main()
