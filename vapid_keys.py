"""
Generate VAPID keys for push notifications
"""

from pywebpush import webpush
import json

def generate_vapid_keys():
    """Generate VAPID keys for push notifications"""
    vapid_keys = webpush.generate_vapid_keys()
    
    print("VAPID Keys Generated Successfully!")
    print("\nAdd these to your .env file:")
    print("=" * 50)
    print(f"VAPID_PUBLIC_KEY={vapid_keys['publicKey']}")
    print(f"VAPID_PRIVATE_KEY={vapid_keys['privateKey']}")
    print("=" * 50)
    
    # Also save to file
    with open('vapid_keys.json', 'w') as f:
        json.dump(vapid_keys, f, indent=2)
    
    print("\nKeys have been saved to vapid_keys.json")
    
    return vapid_keys

if __name__ == '__main__':
    generate_vapid_keys()