#!/usr/bin/env python3
"""
Validate environment variables before starting the application
"""
import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found!")
        print("📝 Create one by copying .env.example:")
        print("   cp .env.example .env")
        return False
    
    print("✅ .env file found")
    return True

def validate_required_vars():
    """Validate required environment variables"""
    required_vars = [
        "BING_API_KEY",
        "HUGGINGFACE_TOKEN"
    ]
    
    optional_vars = [
        "CUDA_VISIBLE_DEVICES",
        "GPU_MEMORY_UTILIZATION", 
        "TENSOR_PARALLEL_SIZE",
        "MAX_MODEL_LEN",
        "CHUNK_SIZE",
        "DEFAULT_TOP_K"
    ]
    
    missing_required = []
    missing_optional = []
    
    # Check required variables
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith("your_"):
            missing_required.append(var)
        else:
            # Show masked value for security
            print(f"✅ {var}: {'*' * min(len(value), 8)}...")
    
    # Check optional variables
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            missing_optional.append(var)
    
    if missing_required:
        print(f"\n❌ Missing required variables: {', '.join(missing_required)}")
        print("Please set these in your .env file")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Optional variables using defaults: {', '.join(missing_optional)}")
    
    print("\n✅ All required environment variables are set!")
    return True

def validate_api_keys():
    """Validate API key formats"""
    bing_key = os.getenv("BING_API_KEY", "")
    hf_token = os.getenv("HUGGINGFACE_TOKEN", "")
    
    if bing_key and not bing_key.startswith("your_"):
        if len(bing_key) < 20:
            print("⚠️  BING_API_KEY seems too short (should be 32+ characters)")
        else:
            print("✅ BING_API_KEY format looks valid")
    
    if hf_token and not hf_token.startswith("hf_your"):
        if not hf_token.startswith("hf_"):
            print("⚠️  HUGGINGFACE_TOKEN should start with 'hf_'")
        else:
            print("✅ HUGGINGFACE_TOKEN format looks valid")

def check_docker_availability():
    """Check if Docker is available"""
    try:
        import subprocess
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Docker is available")
            return True
        else:
            print("❌ Docker is not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Docker is not installed or not in PATH")
        return False

def main():
    """Main validation function"""
    print("🔍 Validating environment configuration...\n")
    
    # Load .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file using python-dotenv")
    except ImportError:
        print("⚠️  python-dotenv not installed, reading from system environment")
        print("   Install with: pip install python-dotenv")
    except Exception as e:
        print(f"⚠️  Could not load .env file: {e}")
    
    print()
    
    # Run validation checks
    env_exists = check_env_file()
    vars_valid = validate_required_vars()
    docker_available = check_docker_availability()
    
    if vars_valid:
        validate_api_keys()
    
    print("\n" + "="*50)
    
    if env_exists and vars_valid and docker_available:
        print("🎉 Environment configuration is valid!")
        print("You can now run: docker-compose up --build")
        sys.exit(0)
    else:
        print("❌ Environment configuration has issues")
        if not env_exists:
            print("  • Create .env file from .env.example")
        if not vars_valid:
            print("  • Set required environment variables")
        if not docker_available:
            print("  • Install Docker and make sure it's running")
        print("\nPlease fix the above issues before starting the application")
        sys.exit(1)

if __name__ == "__main__":
    main()
