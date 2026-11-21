"""
Unit Tests for Security, Encryption and API Key Masking
"""
import unittest
from security.encryption import mask_api_key, encrypt_secret, decrypt_secret


class TestSecurity(unittest.TestCase):
    def test_mask_api_key_lengths(self):
        """Test API key masking across various key lengths and formats"""
        # 1. Standard Finnhub/Twelve Data style key
        key1 = "sk_live_9876543210fedcba"
        masked1 = mask_api_key(key1)
        self.assertTrue(masked1.startswith("sk_l"))
        self.assertTrue(masked1.endswith("dcba"))
        self.assertIn("•", masked1)
        self.assertNotIn("9876543210", masked1)

        # 2. Short key
        key2 = "12345"
        masked2 = mask_api_key(key2)
        self.assertEqual(masked2, "••••••••")

        # 3. Medium 10-char key
        key3 = "c7d24810a9"
        masked3 = mask_api_key(key3)
        self.assertTrue(masked3.startswith("c7"))
        self.assertTrue(masked3.endswith("a9"))
        self.assertIn("•", masked3)

        # 4. Empty string
        self.assertEqual(mask_api_key(""), "••••••••")

    def test_encrypt_decrypt_roundtrip(self):
        """Verify secret can be encrypted for storage and decrypted back accurately"""
        secret = "TwelveData_Secret_Token_#9920!"
        encrypted = encrypt_secret(secret)

        self.assertNotEqual(encrypted, secret)
        self.assertTrue(encrypted.startswith("enc_f:") or encrypted.startswith("enc_x:"))

        decrypted = decrypt_secret(encrypted)
        self.assertEqual(decrypted, secret)

    def test_empty_secret_encryption(self):
        """Empty string should return empty"""
        self.assertEqual(encrypt_secret(""), "")
        self.assertEqual(decrypt_secret(""), "")


if __name__ == "__main__":
    unittest.main()
