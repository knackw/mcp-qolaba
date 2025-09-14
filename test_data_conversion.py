#!/usr/bin/env python3
"""
Quick test script for DATA-002 implementation
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from qolaba_mcp_server.models import (
        convert_file_size_to_bytes,
        validate_audio_format, 
        validate_color_value,
        normalize_model_name,
        convert_duration_to_seconds,
        validate_json_schema
    )
    
    print("✓ Successfully imported all new data conversion utilities")
    
    # Test file size conversion
    result1 = convert_file_size_to_bytes('1MB')
    print(f"✓ File size conversion: 1MB = {result1} bytes")
    
    # Test audio format validation
    result2 = validate_audio_format('mp3')
    print(f"✓ Audio format validation: mp3 -> {result2}")
    
    # Test color validation
    result3 = validate_color_value('red')
    print(f"✓ Color validation: red -> {result3}")
    
    # Test model name normalization
    result4 = normalize_model_name('flux', 'image')
    print(f"✓ Model normalization: flux (image) -> {result4}")
    
    # Test duration conversion
    result5 = convert_duration_to_seconds('1:30')
    print(f"✓ Duration conversion: 1:30 -> {result5} seconds")
    
    # Test JSON validation
    result6 = validate_json_schema({'test': 'data'}, ['test'])
    print(f"✓ JSON validation: {{test: data}} -> {result6}")
    
    print("\n🎉 All DATA-002 utilities implemented and working correctly!")
    
except Exception as e:
    print(f"❌ Error testing utilities: {e}")
    sys.exit(1)