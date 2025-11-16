"""
Test script to verify rate limiter returns proper 429 response instead of 500 error.

This tests the bugfix for HTTPException handling in RateLimitMiddleware.
Educational project - testing for demo purposes.
"""

import asyncio
import sys
import io
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_rate_limit_response():
    """Test that rate limiter returns 429 status code, not 500."""
    from fastapi import Request, HTTPException, status
    from rate_limiter import RateLimiter, RateLimitMiddleware
    from fastapi.responses import JSONResponse
    from unittest.mock import AsyncMock, MagicMock
    
    print("🧪 Testing Rate Limiter Fix...")
    print("-" * 50)
    
    # Create rate limiter instance
    limiter = RateLimiter()
    
    # Override rates for faster testing
    limiter.rates['register'] = {'requests': 2, 'window': 10, 'description': 'Registration attempts'}
    
    # Create mock app
    app = MagicMock()
    middleware = RateLimitMiddleware(app, limiter)
    
    # Create mock request for registration endpoint
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/api/v1/auth/register"
    mock_request.method = "POST"
    mock_request.client.host = "127.0.0.1"
    mock_request.headers.get = MagicMock(return_value=None)
    
    # Mock call_next function
    async def mock_call_next(request):
        return JSONResponse({"message": "Success"})
    
    print("Test 1: First request should succeed")
    try:
        response1 = await middleware.dispatch(mock_request, mock_call_next)
        print(f"✅ Request 1: {response1.status_code} - Success")
    except Exception as e:
        print(f"❌ Request 1 failed unexpectedly: {e}")
        return False
    
    print("\nTest 2: Second request should succeed")
    try:
        response2 = await middleware.dispatch(mock_request, mock_call_next)
        print(f"✅ Request 2: {response2.status_code} - Success")
    except Exception as e:
        print(f"❌ Request 2 failed unexpectedly: {e}")
        return False
    
    print("\nTest 3: Third request should be rate limited with 429")
    try:
        response3 = await middleware.dispatch(mock_request, mock_call_next)
        
        # Check if it's a JSONResponse (not an exception)
        if isinstance(response3, JSONResponse):
            # Parse the status code
            if response3.status_code == 429:
                print(f"✅ Request 3: {response3.status_code} - Rate limited correctly")
                print(f"   Response body: {response3.body.decode() if hasattr(response3, 'body') else 'N/A'}")
                
                # Check for Retry-After header (raw_headers is the actual header storage)
                if hasattr(response3, 'raw_headers'):
                    headers = {k.decode(): v.decode() for k, v in response3.raw_headers}
                    if 'retry-after' in headers or 'Retry-After' in headers:
                        retry_value = headers.get('retry-after', headers.get('Retry-After'))
                        print(f"   ✅ Retry-After header present: {retry_value} seconds")
                    else:
                        print(f"   ⚠️  Note: Retry-After header not in raw_headers (may be set differently)")
                        print(f"   Available headers: {list(headers.keys())}")
                else:
                    print(f"   ℹ️  Info: Response headers not accessible in test (normal for mock)")
                
                return True
            else:
                print(f"❌ Request 3: Expected 429 but got {response3.status_code}")
                return False
        else:
            print(f"❌ Request 3: Expected JSONResponse but got {type(response3)}")
            return False
            
    except HTTPException as e:
        print(f"❌ Request 3: HTTPException still being raised (not converted to response)")
        print(f"   Status Code: {e.status_code}")
        print(f"   Detail: {e.detail}")
        print(f"   This is the OLD BUGGY BEHAVIOR - exception should be converted to JSONResponse")
        return False
    except Exception as e:
        print(f"❌ Request 3 failed with unexpected error: {type(e).__name__}: {e}")
        return False
    
    return False

async def test_rate_limit_block():
    """Test that blocked IPs get proper 429 response."""
    from fastapi import Request
    from rate_limiter import RateLimiter, RateLimitMiddleware
    from fastapi.responses import JSONResponse
    from unittest.mock import AsyncMock, MagicMock
    import time
    
    print("\n" + "=" * 50)
    print("🧪 Testing Blocked IP Response...")
    print("-" * 50)
    
    # Create rate limiter instance
    limiter = RateLimiter()
    
    # Manually block an IP
    test_ip = "192.168.1.100"
    limiter.blocked_ips[test_ip] = time.time() + 3600  # Block for 1 hour
    
    # Create middleware
    app = MagicMock()
    middleware = RateLimitMiddleware(app, limiter)
    
    # Create mock request
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/api/v1/auth/login"
    mock_request.method = "POST"
    mock_request.client.host = test_ip
    mock_request.headers.get = MagicMock(return_value=None)
    
    async def mock_call_next(request):
        return JSONResponse({"message": "Success"})
    
    print("Test: Blocked IP should receive 429 response")
    try:
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        if isinstance(response, JSONResponse) and response.status_code == 429:
            print(f"✅ Blocked IP: {response.status_code} - Properly rejected")
            return True
        else:
            print(f"❌ Blocked IP: Expected 429 JSONResponse but got {type(response)} with status {getattr(response, 'status_code', 'N/A')}")
            return False
            
    except Exception as e:
        print(f"❌ Blocked IP test failed: {type(e).__name__}: {e}")
        return False

async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🔧 RATE LIMITER BUGFIX VERIFICATION TEST")
    print("=" * 60)
    print("Testing that rate limiter returns 429 instead of 500\n")
    
    test1_passed = await test_rate_limit_response()
    test2_passed = await test_rate_limit_block()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"Rate Limit Response Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Blocked IP Response Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED - Bugfix verified!")
        print("Rate limiter now properly returns 429 responses.")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - Review the output above")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
