"""
Property-based tests for configuration validation.

**Feature: migration-wassenger-2025, Property 6: Configuration Validation**
**Validates: Requirements 1.1, 1.2, 5.4**
"""
import pytest
from hypothesis import given, settings as hyp_settings, strategies as st
from app.config import Settings

# Configure Hypothesis for CI: minimum 100 iterations
hyp_settings.register_profile("ci", max_examples=100)
hyp_settings.load_profile("ci")


# Strategy for non-empty strings (valid config values)
non_empty_strings = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())

# Strategy for empty or whitespace-only strings (invalid config values)
empty_or_whitespace = st.sampled_from(["", " ", "  ", "\t", "\n", "   \t\n"])


class TestConfigurationValidationProperty:
    """
    Property 6: Configuration Validation
    
    *For any* configuration where WASSENGER_API_KEY or WASSENGER_DEVICE_ID is empty 
    or missing, validation should raise a ValueError with a message containing the 
    name of the missing variable.
    
    **Feature: migration-wassenger-2025, Property 6: Configuration Validation**
    **Validates: Requirements 1.1, 1.2, 5.4**
    """

    @given(
        api_key=empty_or_whitespace,
        device_id=non_empty_strings
    )
    def test_missing_api_key_raises_error_with_variable_name(self, api_key: str, device_id: str):
        """
        **Feature: migration-wassenger-2025, Property 6: Configuration Validation**
        **Validates: Requirements 1.1, 1.2, 5.4**
        
        For any empty/whitespace API key with valid device ID,
        validation should raise ValueError mentioning WASSENGER_API_KEY.
        """
        # Create settings with empty API key
        settings_obj = Settings(
            WASSENGER_API_KEY=api_key,
            WASSENGER_DEVICE_ID=device_id,
            SUPABASE_URL="https://test.supabase.co",
            SUPABASE_KEY="test-key",
            DATABASE_URL="postgresql://test:test@localhost/test",
            SECRET_KEY="test-secret-key"
        )
        
        # Validation should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            settings_obj.validate_wassenger_config()
        
        # Error message should contain the missing variable name
        assert "WASSENGER_API_KEY" in str(exc_info.value)

    @given(
        api_key=non_empty_strings,
        device_id=empty_or_whitespace
    )
    def test_missing_device_id_raises_error_with_variable_name(self, api_key: str, device_id: str):
        """
        **Feature: migration-wassenger-2025, Property 6: Configuration Validation**
        **Validates: Requirements 1.1, 1.2, 5.4**
        
        For any valid API key with empty/whitespace device ID,
        validation should raise ValueError mentioning WASSENGER_DEVICE_ID.
        """
        settings_obj = Settings(
            WASSENGER_API_KEY=api_key,
            WASSENGER_DEVICE_ID=device_id,
            SUPABASE_URL="https://test.supabase.co",
            SUPABASE_KEY="test-key",
            DATABASE_URL="postgresql://test:test@localhost/test",
            SECRET_KEY="test-secret-key"
        )
        
        with pytest.raises(ValueError) as exc_info:
            settings_obj.validate_wassenger_config()
        
        assert "WASSENGER_DEVICE_ID" in str(exc_info.value)

    @given(
        api_key=empty_or_whitespace,
        device_id=empty_or_whitespace
    )
    def test_both_missing_raises_error_with_both_variable_names(self, api_key: str, device_id: str):
        """
        **Feature: migration-wassenger-2025, Property 6: Configuration Validation**
        **Validates: Requirements 1.1, 1.2, 5.4**
        
        For any configuration with both variables empty/whitespace,
        validation should raise ValueError mentioning both variable names.
        """
        settings_obj = Settings(
            WASSENGER_API_KEY=api_key,
            WASSENGER_DEVICE_ID=device_id,
            SUPABASE_URL="https://test.supabase.co",
            SUPABASE_KEY="test-key",
            DATABASE_URL="postgresql://test:test@localhost/test",
            SECRET_KEY="test-secret-key"
        )
        
        with pytest.raises(ValueError) as exc_info:
            settings_obj.validate_wassenger_config()
        
        error_message = str(exc_info.value)
        assert "WASSENGER_API_KEY" in error_message
        assert "WASSENGER_DEVICE_ID" in error_message

    @given(
        api_key=non_empty_strings,
        device_id=non_empty_strings
    )
    def test_valid_config_does_not_raise(self, api_key: str, device_id: str):
        """
        **Feature: migration-wassenger-2025, Property 6: Configuration Validation**
        **Validates: Requirements 1.1, 1.2, 5.4**
        
        For any configuration with both variables non-empty,
        validation should not raise any error.
        """
        settings_obj = Settings(
            WASSENGER_API_KEY=api_key,
            WASSENGER_DEVICE_ID=device_id,
            SUPABASE_URL="https://test.supabase.co",
            SUPABASE_KEY="test-key",
            DATABASE_URL="postgresql://test:test@localhost/test",
            SECRET_KEY="test-secret-key"
        )
        
        # Should not raise any exception
        settings_obj.validate_wassenger_config()
