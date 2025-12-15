from app import create_app
import sys

try:
    app = create_app()
    print("Application created successfully.")
    
    print("\n--- Registered Routes ---")
    found = False
    for rule in app.url_map.iter_rules():
        print(f"{rule} -> {rule.endpoint}")
        if rule.endpoint == 'main.catalog':
            found = True
            
    if found:
        print("\nSUCCESS: 'main.catalog' route IS registered!")
    else:
        print("\nFAILURE: 'main.catalog' route is MISSING.")
        sys.exit(1)
        
except Exception as e:
    print(f"\nERROR: Could not create app: {e}")
    sys.exit(1)
