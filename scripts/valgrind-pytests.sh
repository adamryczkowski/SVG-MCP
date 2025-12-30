#!/usr/bin/env bash
# valgrind-pytests.sh - Run pytest under valgrind for memory leak detection
#
# This is a manual pre-commit hook for detecting memory leaks in native extensions.
# It requires valgrind to be installed on the system.
#
# Usage:
#   pre-commit run valgrind-pytests --hook-stage manual
#   # or directly:
#   bash scripts/valgrind-pytests.sh
#
# Note: This is primarily useful for projects with C extensions or when debugging
# memory issues in the Python interpreter itself. For pure Python projects,
# this hook may not provide significant value.

set -euo pipefail

# Check if valgrind is installed
if ! command -v valgrind >/dev/null 2>&1; then
	echo "valgrind is not installed. Skipping memory check."
	echo "Install with: sudo apt-get install valgrind"
	exit 0
fi

# Run pytest under valgrind
# --suppressions can be added for known Python interpreter leaks
echo "Running pytest under valgrind (this may take a while)..."
valgrind \
	--leak-check=full \
	--show-leak-kinds=definite,possible \
	--errors-for-leak-kinds=definite \
	--error-exitcode=1 \
	--log-file=valgrind-report.txt \
	poetry run python -m pytest tests/ -x -q

echo "Valgrind report saved to valgrind-report.txt"
