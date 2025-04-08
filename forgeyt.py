# forgeyt.py (Corrected Launcher)
"""Initiating functions for ForgeYT"""
import os
import sys
import traceback # Added for better error reporting

# --- Path Setup ---
# Add the directory containing forgeyt.py (the project root) to the Python path.
# This helps ensure Python can find the 'app', 'utils', and 'vars' packages.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added project root to sys.path: {project_root}")

# --- Import and Run ---
try:
    # Import the main starter function from the app package
    # This function should reside in app/__init__.py
    from app import start_app
except ImportError as e:
    print("Fatal Error: Could not import 'start_app' from the 'app' package.", file=sys.stderr)
    print(f"Details: {e}", file=sys.stderr)
    print(f"Current sys.path: {sys.path}", file=sys.stderr)
    print("Ensure the 'app' directory exists and contains an '__init__.py' defining 'start_app'.", file=sys.stderr)
    traceback.print_exc() # Print detailed traceback
    sys.exit(1) # Exit if the core app component cannot be imported
except Exception as e:
    print(f"An unexpected error occurred importing from 'app': {e}", file=sys.stderr)
    traceback.print_exc() # Print detailed traceback
    sys.exit(1)


if __name__ == "__main__":
    # Call the function that initializes and runs the Qt application
    print("Starting ForgeYT...")
    try:
        start_app()
    except Exception as e:
        # Catch any unexpected errors during app execution
        print(f"Fatal Error during application execution: {e}", file=sys.stderr)
        traceback.print_exc() # Print detailed traceback
        # Optional: Add a simple GUI error popup here if desired before exiting
        sys.exit(1)