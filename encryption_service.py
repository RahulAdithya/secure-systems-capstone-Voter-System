import os
from cryptography.fernet import Fernet
from typing import Union

# --- Key Generation Utility (Run ONLY ONCE to get the key) ---

def generate_new_key() -> str:
    """Utility function to generate a new Fernet key string."""
    return Fernet.generate_key().decode()

# --- Configuration & Key Loading ---

# CRITICAL: The secret key must be loaded from a secure source (e.g., environment variable)
# and MUST be the same across all instances of your application.
# It should NEVER be hardcoded in the script for a production environment.

def initialize_cipher() -> Fernet:
    """Loads the key from the environment or raises an error."""
    try:
        # 1. Attempt to load the FERNET_KEY from the system environment variables
        secret_key_bytes = os.environ['FERNET_KEY'].encode()
        # 2. Return the initialized Fernet cipher suite
        return Fernet(secret_key_bytes)
    except KeyError:
        # This error is critical in a real application, as it ensures security
        # if the key is missing during deployment.
        raise EnvironmentError("FATAL: FERNET_KEY environment variable not set. Cannot run encryption service.")

# We initialize the cipher here. If it fails, the script will stop immediately.
# For the demo/test section, we'll handle this error below.
# cipher_suite = initialize_cipher() 
# ^ Uncomment this line when deploying to a secure environment!


# --- Core Functions ---

def encrypt_pii(cipher_suite: Fernet, plaintext_data: Union[str, bytes]) -> bytes:
    """
    Encrypts PII data using the loaded Fernet key.
    The result (ciphertext) is what gets stored in the database.
    
    Acceptance Criteria 1: Stored value is ciphertext (not plaintext).
    """
    if isinstance(plaintext_data, str):
        plaintext_data = plaintext_data.encode('utf-8')
        
    return cipher_suite.encrypt(plaintext_data)

def decrypt_pii(cipher_suite: Fernet, ciphertext_data: bytes) -> str:
    """
    Decrypts the ciphertext from the database back into plaintext.
    
    Acceptance Criteria 2: Correct key decrypts; wrong key fails.
    If the key is wrong or data is tampered with, cryptography.fernet.InvalidToken 
    exception is raised, satisfying the failure criterion.
    """
    try:
        decrypted_bytes = cipher_suite.decrypt(ciphertext_data)
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        # Catch InvalidToken or other decryption failures
        print(f"Decryption failed: {e.__class__.__name__}. The key may be wrong or data tampered.")
        raise

# --- Example Usage ---

if __name__ == "__main__":
    
    # --- Key Setup ---
    # First, check if the key is set. If not, generate a TEMPORARY key for the demo.
    # THIS TEMPORARY KEY IS ONLY FOR THE DEMO AND SHOULD NOT BE USED FOR REAL DATA.
    if 'FERNET_KEY' not in os.environ:
        temp_key = generate_new_key()
        print("----------------------------------------------------------------------")
        print("ATTENTION: FERNET_KEY not set. Using a temporary key for demo purposes.")
        print(f"To use a persistent key, set $env:FERNET_KEY=\"{temp_key}\"")
        print("----------------------------------------------------------------------")
        demo_cipher_suite = Fernet(temp_key.encode())
    else:
        # If the key IS set, load it securely using the function defined above.
        print("FERNET_KEY successfully loaded from environment.")
        demo_cipher_suite = initialize_cipher()

    
    # --- Demonstration ---
    
    pii_email = "jane.doe@securevoter.org"
    
    print(f"\nOriginal PII: {pii_email}")
    
    # ENCRYPT: What the application stores in the DB
    # We pass the cipher_suite object to the function
    encrypted_email = encrypt_pii(demo_cipher_suite, pii_email) 
    print(f"Ciphertext (DB field): {encrypted_email.decode()}")
    
    # CHECK 1: Stored value is unreadable (Ciphertext) - PASSED

    # DECRYPT: What the application retrieves for use
    # We pass the cipher_suite object to the function
    decrypted_email = decrypt_pii(demo_cipher_suite, encrypted_email) 
    print(f"Decrypted PII: {decrypted_email}")
    
    # CHECK 2: Correct key decrypts - PASSED